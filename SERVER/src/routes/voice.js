const express = require("express");
const multer = require("multer");
const { askLLM } = require("../services/llm");
const cache = require("../services/cache");

const upload = multer({ storage: multer.memoryStorage() });
const router = express.Router();

router.post("/", upload.single("audio"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "no audio" });

  // Placeholder: integrate Whisper/OpenAI Speech-to-Text
  const transcript = "[transcribed speech here]";
  const answer = await askLLM(transcript);
  cache.set("lastAnswer", answer);
  res.json({ transcript, answer });
});

module.exports = router;
