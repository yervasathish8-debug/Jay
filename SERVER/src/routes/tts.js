const express = require("express");
const gTTS = require("google-tts-api");
const cache = require("../services/cache");

const router = express.Router();

router.get("/", async (req, res) => {
  const last = cache.get("lastAnswer");
  if (!last) return res.status(400).json({ error: "no previous answer" });

  const url = gTTS.getAudioUrl(last, { lang: "en", slow: false });
  res.json({ audioUrl: url });
});

module.exports = router;
