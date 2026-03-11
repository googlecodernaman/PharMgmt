"""Lightweight ML models for pharmacy bill parsing.

Two models:
1. BillTypeClassifier — CNN-based document classifier (< 5MB)
2. FieldExtractor — BiLSTM-CRF for token-level field extraction (< 20MB)

Both designed for low-end CPU inference via ONNX export.
"""

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class BillTypeClassifier(nn.Module):
    """Small CNN text classifier for bill type detection.

    Architecture:
        Embedding → [Conv1d + ReLU + MaxPool] × 3 → FC → Softmax

    Input: token ID sequences (padded)
    Output: bill type probabilities

    Total params: ~500K (< 2MB)
    """

    def __init__(
        self,
        vocab_size: int,
        num_classes: int = 4,
        embed_dim: int = 64,
        num_filters: int = 64,
        filter_sizes: tuple = (2, 3, 4),
        dropout: float = 0.3,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, fs) for fs in filter_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_filters * len(filter_sizes), num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Token IDs [batch, seq_len]

        Returns:
            Logits [batch, num_classes]
        """
        emb = self.embedding(x).transpose(1, 2)  # [B, E, L]
        conv_outs = []
        for conv in self.convs:
            c = F.relu(conv(emb))  # [B, F, L']
            c = c.max(dim=2).values  # [B, F]
            conv_outs.append(c)
        cat = torch.cat(conv_outs, dim=1)  # [B, F*3]
        return self.fc(self.dropout(cat))


class CRFLayer(nn.Module):
    """Conditional Random Field layer for sequence labeling.

    Implements a first-order linear-chain CRF for BIO tag decoding.
    """

    def __init__(self, num_tags: int):
        super().__init__()
        self.num_tags = num_tags
        self.transitions = nn.Parameter(torch.randn(num_tags, num_tags))
        self.start_transitions = nn.Parameter(torch.randn(num_tags))
        self.end_transitions = nn.Parameter(torch.randn(num_tags))

    def forward(
        self, emissions: torch.Tensor, tags: torch.Tensor, mask: torch.Tensor
    ) -> torch.Tensor:
        """Compute negative log-likelihood loss.

        Args:
            emissions: [batch, seq_len, num_tags]
            tags: [batch, seq_len] ground truth tag indices
            mask: [batch, seq_len] boolean mask (1=valid, 0=pad)

        Returns:
            Scalar NLL loss.
        """
        numerator = self._score_sentence(emissions, tags, mask)
        denominator = self._forward_algorithm(emissions, mask)
        return (denominator - numerator).mean()

    def decode(self, emissions: torch.Tensor, mask: torch.Tensor) -> list[list[int]]:
        """Viterbi decode best tag sequences.

        Args:
            emissions: [batch, seq_len, num_tags]
            mask: [batch, seq_len]

        Returns:
            List of tag index lists.
        """
        batch_size, seq_len, _ = emissions.shape
        all_tags = []

        for b in range(batch_size):
            length = int(mask[b].sum().item())
            em = emissions[b, :length]

            # Initialize
            score = self.start_transitions + em[0]
            history = []

            for t in range(1, length):
                broadcast_score = score.unsqueeze(1)  # [tags, 1]
                broadcast_emission = em[t].unsqueeze(0)  # [1, tags]
                next_score = broadcast_score + self.transitions + broadcast_emission
                next_score, indices = next_score.max(dim=0)
                history.append(indices)
                score = next_score

            score += self.end_transitions
            _, best_last = score.max(dim=0)
            best_tags = [best_last.item()]

            for hist in reversed(history):
                best_tags.append(hist[best_tags[-1]].item())
            best_tags.reverse()

            all_tags.append(best_tags)

        return all_tags

    def _score_sentence(
        self, emissions: torch.Tensor, tags: torch.Tensor, mask: torch.Tensor
    ) -> torch.Tensor:
        batch_size, seq_len, _ = emissions.shape
        score = self.start_transitions[tags[:, 0]]
        score += emissions[:, 0].gather(1, tags[:, 0].unsqueeze(1)).squeeze(1)

        for t in range(1, seq_len):
            m = mask[:, t].float()
            emit = emissions[:, t].gather(1, tags[:, t].unsqueeze(1)).squeeze(1)
            trans = self.transitions[tags[:, t - 1], tags[:, t]]
            score += (emit + trans) * m

        # End transitions
        last_idx = mask.long().sum(dim=1) - 1
        last_tags = tags.gather(1, last_idx.unsqueeze(1)).squeeze(1)
        score += self.end_transitions[last_tags]

        return score

    def _forward_algorithm(
        self, emissions: torch.Tensor, mask: torch.Tensor
    ) -> torch.Tensor:
        batch_size, seq_len, num_tags = emissions.shape
        score = self.start_transitions + emissions[:, 0]

        for t in range(1, seq_len):
            m = mask[:, t].unsqueeze(1).float()
            broadcast_score = score.unsqueeze(2)
            broadcast_emission = emissions[:, t].unsqueeze(1)
            next_score = broadcast_score + self.transitions + broadcast_emission
            next_score = torch.logsumexp(next_score, dim=1)
            score = next_score * m + score * (1 - m)

        score += self.end_transitions
        return torch.logsumexp(score, dim=1)


class FieldExtractor(nn.Module):
    """BiLSTM-CRF model for token-level field extraction.

    Architecture:
        [Token Features + Char Embedding] → BiLSTM → Linear → CRF

    Input: hand-crafted token features (11-dim) + character embeddings
    Output: BIO tag sequence

    Total params: ~2M (< 10MB)
    """

    def __init__(
        self,
        num_tags: int,
        feature_dim: int = 11,
        char_vocab_size: int = 256,
        char_embed_dim: int = 16,
        char_hidden_dim: int = 32,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.num_tags = num_tags

        # Character-level encoder
        self.char_embedding = nn.Embedding(char_vocab_size, char_embed_dim, padding_idx=0)
        self.char_lstm = nn.LSTM(
            char_embed_dim, char_hidden_dim // 2,
            batch_first=True, bidirectional=True,
        )

        # Combined input: features + char encoding
        input_dim = feature_dim + char_hidden_dim

        # BiLSTM encoder
        self.lstm = nn.LSTM(
            input_dim, hidden_dim // 2,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        self.dropout = nn.Dropout(dropout)
        self.hidden2tag = nn.Linear(hidden_dim, num_tags)
        self.crf = CRFLayer(num_tags)

    def _encode_chars(self, char_ids: torch.Tensor) -> torch.Tensor:
        """Encode character sequences per token.

        Args:
            char_ids: [batch, seq_len, max_char_len]

        Returns:
            [batch, seq_len, char_hidden_dim]
        """
        batch, seq_len, max_char = char_ids.shape
        flat = char_ids.view(batch * seq_len, max_char)

        emb = self.char_embedding(flat)
        _, (h, _) = self.char_lstm(emb)
        # Concat forward and backward
        h = torch.cat([h[0], h[1]], dim=1)  # [B*L, char_hidden]
        return h.view(batch, seq_len, -1)

    def _get_emissions(
        self, features: torch.Tensor, char_ids: torch.Tensor
    ) -> torch.Tensor:
        """Compute emission scores.

        Args:
            features: [batch, seq_len, feature_dim]
            char_ids: [batch, seq_len, max_char_len]

        Returns:
            [batch, seq_len, num_tags]
        """
        char_enc = self._encode_chars(char_ids)
        combined = torch.cat([features, char_enc], dim=2)
        lstm_out, _ = self.lstm(combined)
        lstm_out = self.dropout(lstm_out)
        return self.hidden2tag(lstm_out)

    def forward(
        self,
        features: torch.Tensor,
        char_ids: torch.Tensor,
        tags: torch.Tensor,
        mask: torch.Tensor,
    ) -> torch.Tensor:
        """Compute CRF loss.

        Args:
            features: [batch, seq_len, feature_dim]
            char_ids: [batch, seq_len, max_char_len]
            tags: [batch, seq_len]
            mask: [batch, seq_len]

        Returns:
            Scalar loss.
        """
        emissions = self._get_emissions(features, char_ids)
        return self.crf(emissions, tags, mask)

    def predict(
        self, features: torch.Tensor, char_ids: torch.Tensor, mask: torch.Tensor
    ) -> list[list[int]]:
        """Predict best tag sequences via Viterbi decoding.

        Args:
            features: [batch, seq_len, feature_dim]
            char_ids: [batch, seq_len, max_char_len]
            mask: [batch, seq_len]

        Returns:
            List of predicted tag index lists.
        """
        emissions = self._get_emissions(features, char_ids)
        return self.crf.decode(emissions, mask)
