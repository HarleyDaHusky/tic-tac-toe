const Ably = require('ably');

module.exports = async (req, res) => {
  try {
    if (!process.env.ABLY_API_KEY) {
      res.status(500).json({ error: 'Missing ABLY_API_KEY env var' });
      return;
    }
    const client = new Ably.Rest({ key: process.env.ABLY_API_KEY });
    const tokenRequest = await new Promise((resolve, reject) => {
      client.auth.createTokenRequest((err, tokenReq) => {
        if (err) reject(err);
        else resolve(tokenReq);
      });
    });
    res.setHeader('Content-Type', 'application/json');
    res.status(200).json(tokenRequest);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  }
};