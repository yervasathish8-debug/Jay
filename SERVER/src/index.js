require("dotenv").config();
const express = require("express");
const helmet = require("helmet");
const cors = require("cors");
const rateLimit = require("express-rate-limit");

const textRoute = require("./routes/text");
const ocrRoute = require("./routes/ocr");
const voiceRoute = require("./routes/voice");
const ttsRoute = require("./routes/tts");

const app = express();
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || "*" }));
app.use(express.json({ limit: "10mb" }));

// Rate limit
app.use("/api/", rateLimit({ windowMs: 60_000, max: 30 }));

// Routes
app.use("/api/text", textRoute);
app.use("/api/ocr", ocrRoute);
app.use("/api/voice-to-text", voiceRoute);
app.use("/api/text-to-speech", ttsRoute);

app.get("/health", (_, res) => res.json({ ok: true }));

const PORT = process.env.PORT || 3000;
app.get("/ping", (req, res) => {
  res.json({ message: "pong from server" });
});
app.listen(PORT, () => console.log(`✅ Server running on ${PORT}`));
