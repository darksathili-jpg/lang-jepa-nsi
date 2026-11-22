"""Pilote CPU utilisant les classes du projet LANG-JEPA à la révision P2."""

from itertools import chain
from pathlib import Path
import time

import torch
from torch.nn import functional as F
from transformers import AutoTokenizer

from src.common.config import LANGJEPAConfig
from src.common.pooling import masked_mean
from src.decoder.concept_extractor import ConceptExtractor
from src.decoder.models import ConceptDecoder, DecoderConfig
from src.encoder.ema import EMAEncoder
from src.encoder.models import TextPredictor, TextTransformer


class Pilot:
    def __init__(self, assets, source, settings):
        self.settings = settings
        torch.set_num_threads(settings["threads"])
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(settings["seed"])

        self.config = LANGJEPAConfig.from_yaml(str(source / "src/encoder/configs/base_lang_config.yaml"))
        tokenizer_path = assets / "roberta-base"
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
        self.config.data.tokenizer = self.tokenizer
        self.config.data.tokenizer_path = str(tokenizer_path)
        cfg = self.config.model
        cfg.pretrained = False
        cfg.embed_dim = cfg.pred_dim = settings["width"]
        cfg.num_layers = 1
        cfg.num_heads = 4
        cfg.max_length = settings["max_input_tokens"]
        self.encoder = TextTransformer(self.config)
        self.predictor = TextPredictor(cfg.embed_dim, cfg.pred_dim)
        self.target = EMAEncoder(self.encoder)
        self.extractor = None
        self.decoder = None

    def tokens(self, texts):
        item = self.tokenizer(texts, padding=True, truncation=False, return_tensors="pt")
        if item["input_ids"].shape[1] > self.settings["max_input_tokens"]:
            raise ValueError("Un segment dépasse le budget du pilote.")
        return item["input_ids"], item["attention_mask"]

    @staticmethod
    def pooled(encoder, ids, mask):
        return F.normalize(masked_mean(encoder(ids, mask), mask), dim=-1)

    def predict(self, ids, mask):
        return F.normalize(self.predictor(self.encoder(ids, mask), mask), dim=-1)

    @torch.inference_mode()
    def represent(self, texts, kind, batch_size=1):
        self.encoder.eval()
        self.predictor.eval()
        output = []
        for start in range(0, len(texts), batch_size):
            ids, mask = self.tokens(texts[start:start + batch_size])
            if kind == "predicted":
                vector = self.predict(ids, mask)
            elif kind == "online" and self.extractor is not None:
                vector = self.extractor(ids, mask)
            else:
                vector = self.pooled(self.target if kind == "target" else self.encoder, ids, mask)
            output.append(vector)
        return torch.cat(output)

    def batches(self, examples, steps):
        used = 0
        batch = self.settings["train_batch"]
        while used < steps:
            order = torch.randperm(len(examples)).tolist()
            for start in range(0, len(order), batch):
                yield [examples[index] for index in order[start:start + batch]]
                used += 1
                if used == steps:
                    return

    def train_encoder(self, pairs):
        self.encoder.train()
        self.predictor.train()
        optimizer = torch.optim.AdamW(
            chain(self.encoder.parameters(), self.predictor.parameters()), lr=self.settings["encoder_lr"],
            weight_decay=self.settings["weight_decay"],
        )
        losses = []
        for batch in self.batches(pairs, self.settings["encoder_steps"]):
            context = self.tokens([item.context for item in batch])
            target = self.tokens([item.target for item in batch])
            with torch.no_grad():
                embedding = self.pooled(self.target, *target)
            loss = F.smooth_l1_loss(self.predict(*context), embedding)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            self.target.update(self.encoder, momentum=self.settings["momentum"])
            losses.append(loss.item())
        return losses

    def decoder_loss(self, concepts, ids):
        logits = self.decoder(concepts, target_ids=ids)
        return F.cross_entropy(
            logits.flatten(0, 1), ids[:, 1:].reshape(-1), ignore_index=self.tokenizer.pad_token_id,
        )

    def train_decoder(self, texts):
        width = self.settings["width"]
        self.decoder_config = DecoderConfig.from_tokenizer(
            self.tokenizer, width, hidden_dim=width, num_layers=1, num_heads=4,
            max_length=self.settings["max_input_tokens"],
        )
        self.decoder = ConceptDecoder(self.decoder_config, self.tokenizer)
        self.extractor = ConceptExtractor(self.encoder, normalize=True)
        concepts = self.represent(texts, "online").clone()
        optimizer = torch.optim.AdamW(
            self.decoder.parameters(), lr=self.settings["decoder_lr"], weight_decay=self.settings["weight_decay"],
        )
        losses = []
        for batch in self.batches(list(range(len(texts))), self.settings["decoder_steps"]):
            ids, _ = self.tokens([texts[index] for index in batch])
            loss = self.decoder_loss(concepts[batch], ids)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        return losses

    @torch.inference_mode()
    def decode(self, text, concept, control):
        self.decoder.eval()
        ids, _ = self.tokens([text])
        started = time.perf_counter()
        generated = self.decoder.generate(
            concept, self.tokenizer, do_sample=False, max_length=self.settings["max_new_tokens"] + 1,
        )[0]
        latency = time.perf_counter() - started
        return {
            "reference": text, "generated": generated, "seconds": latency,
            "teacher_forced_ce": self.decoder_loss(concept, ids).item(),
            "swapped_concept_ce": self.decoder_loss(control, ids).item(),
        }

    def save(self, directory: Path):
        import yaml

        config = self.config.model_dump(exclude={"data": {"tokenizer"}})
        config["data"]["tokenizer_path"] = "roberta-base"
        (directory / "encoder_config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
        torch.save({
            "encoder": self.encoder.state_dict(),
            "predictor": self.predictor.state_dict(),
            "target_encoder": self.target.state_dict(),
        }, directory / "encoder.pth")
        torch.save({
            "model_state_dict": self.decoder.state_dict(), "config": self.decoder_config,
        }, directory / "decoder.pt")
