import express, { type Router } from 'express';
import { authenticate, type AuthRequest } from './middleware';

interface Invoice {
  id: string;
  organization_id: string;
  amount: number;
  date: string;
  pdfData: Buffer;
}

// Database accessor — assume backed by a real DB in production.
async function getInvoiceById(id: string): Promise<Invoice | null> {
  // Stub for the audit fixture: returns null. The fixture's purpose is
  // to expose the request path, not to populate data. Treat as if any
  // valid invoice id resolves to an invoice in the production DB.
  void id;
  return null;
}

async function exportInvoicePDF(invoice: Invoice): Promise<Buffer> {
  return invoice.pdfData;
}

const router: Router = express.Router();

// POST /api/invoices/export
// Body: { invoiceId: string }
// Response: application/pdf
router.post('/export', authenticate, async (req: AuthRequest, res) => {
  const { invoiceId } = req.body as { invoiceId?: string };
  if (!invoiceId) {
    res.status(400).json({ error: 'invoiceId required' });
    return;
  }
  const invoice = await getInvoiceById(invoiceId);
  if (!invoice) {
    res.status(404).json({ error: 'invoice not found' });
    return;
  }
  const pdf = await exportInvoicePDF(invoice);
  res.setHeader('Content-Type', 'application/pdf');
  res.send(pdf);
});

export default router;
