const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const Tesseract = require('tesseract.js');
const gTTS = require('gtts');

const app = express();
const upload = multer();

// Middleware
app.use(cors());
app.use(bodyParser.json());

// AI Model Endpoint Simulation
const AI_MODEL_URL = 'your-ai-model-endpoint'; // Replace with your AI model endpoint

// Handle Text Input
app.post('/api/text', async (req, res) => {
    const { text } = req.body;
    try {
        const response = await axios.post(AI_MODEL_URL, { text });
        res.json(response.data);
    } catch (error) {
        res.status(500).send('Error communicating with AI model.');
    }
});

// Handle OCR
app.post('/api/ocr', upload.single('image'), async (req, res) => {
    const imageBuffer = req.file.buffer;
    try {
        const { data: { text } } = await Tesseract.recognize(imageBuffer, 'eng');
        res.json({ text });
    } catch (error) {
        res.status(500).send('Error processing image.');
    }
});

// Handle Voice Input
app.post('/api/voice', upload.single('audio'), async (req, res) => {
    const audioBuffer = req.file.buffer;
    // Replace with actual voice-to-text service
    // const text = await voiceToTextService(audioBuffer);
    const text = 'Recognized text'; // Temporary placeholder.
    
    res.json({ text });
});

// Handle Text-to-Speech
app.post('/api/text-to-speech', (req, res) => {
    const { text } = req.body;
    const gtts = new gTTS(text, 'en');
    const filename = 'output.mp3';
    
    gtts.save(filename, function (err, result) {
        if (err) { 
            res.status(500).send('Error converting text to speech.');
        }
        res.download(filename); // Send the audio file to the client
    });
});

// Start Server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});