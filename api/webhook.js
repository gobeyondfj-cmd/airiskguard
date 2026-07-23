export const config = {
  api: {
    bodyParser: false, // Stripe requires raw body for signature verification
  },
};

async function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
  const sig = req.headers['stripe-signature'];
  const rawBody = await getRawBody(req);

  let event;
  try {
    event = stripe.webhooks.constructEvent(
      rawBody,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).json({ error: `Webhook error: ${err.message}` });
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const customerEmail = session.customer_details?.email || 'unknown';
    const customerId = session.customer;
    const subscriptionId = session.subscription;

    console.log(JSON.stringify({
      event: 'new_team_subscriber',
      email: customerEmail,
      customer_id: customerId,
      subscription_id: subscriptionId,
      amount: session.amount_total,
      currency: session.currency,
      ts: new Date().toISOString(),
    }));
  }

  if (event.type === 'customer.subscription.deleted') {
    const sub = event.data.object;
    console.log(JSON.stringify({
      event: 'subscription_cancelled',
      customer_id: sub.customer,
      subscription_id: sub.id,
      ts: new Date().toISOString(),
    }));
  }

  res.status(200).json({ received: true });
}
