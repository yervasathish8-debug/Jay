const express = require("express");
const multer = require("multer");
const Tesseract = require("tesseract.js");
const { askLLM } = require("../services/llm");
const cache = require("../services/cache");

const upload = multer({ storage: multer.memoryStorage() });
const router = express.Router();

router.post("/", upload.single("image"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "no image" });

  const { data: { text } } = await Tesseract.recognize(req.file.buffer, "eng");
  const answer = await askLLM(text);
  cache.set("lastAnswer", answer);
  res.json({ text, answer });
});

module.exports = router;
