import crypto from 'crypto';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { session_id } = req.query;
  if (!session_id || !session_id.startsWith('cs_')) {
    return res.status(400).json({ error: 'Invalid session ID' });
  }

  const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

  let session;
  try {
    session = await stripe.checkout.sessions.retrieve(session_id);
  } catch (err) {
    return res.status(400).json({ error: 'Could not verify payment' });
  }

  if (session.payment_status !== 'paid') {
    return res.status(402).json({ error: 'Payment not completed' });
  }

  // Generate a deterministic license key from the subscription ID + secret
  // Same subscription always gets the same key — idempotent
  const subscriptionId = session.subscription || session.id;
  const secret = process.env.LICENSE_SECRET || process.env.STRIPE_SECRET_KEY;
  const licenseKey = crypto
    .createHmac('sha256', secret)
    .update(subscriptionId)
    .digest('hex')
    .slice(0, 32)
    .toUpperCase()
    .replace(/(.{8})/g, '$1-')
    .slice(0, -1); // format: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX

  return res.status(200).json({
    license_key: licenseKey,
    customer_email: session.customer_details?.email || '',
    subscription_id: subscriptionId,
    plan: 'team',
  });
}
