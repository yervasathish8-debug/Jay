const express = require("express");
const { askLLM } = require("../services/llm");
const cache = require("../services/cache");
const router = express.Router();

router.post("/", async (req, res) => {
  const text = req.body.text;
  if (!text) return res.status(400).json({ error: "no text" });

  const answer = await askLLM(text);
  cache.set("lastAnswer", answer);
  res.json({ answer });
});

module.exports = router;
