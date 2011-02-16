from django.core.urlresolvers import reverse
from django.test import TestCase
from project.models import Proposal, PROPOSAL_STATE_DRAFT, ROW_CATEGORY_SERVICE, \
    ROW_CATEGORY_PRODUCT, PROPOSAL_STATE_BALANCED, PROPOSAL_STATE_ACCEPTED
from accounts.models import INVOICE_STATE_EDITED, Invoice, InvoiceRow, \
    INVOICE_STATE_SENT, InvoiceRowAmountError, PAYMENT_TYPE_CHECK, \
    PAYMENT_TYPE_CASH, Expense, INVOICE_STATE_PAID
from django.contrib.auth.models import User
from django.utils import simplejson
from django.utils.formats import localize
import datetime
import hashlib

class ExpensePermissionTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.expense1 = Expense.objects.create(date=datetime.date(2010, 1, 1),
                                               reference='ABCD',
                                               amount='100.0',
                                               payment_type=PAYMENT_TYPE_CHECK,
                                               description='First expense',
                                               owner_id=1)
        self.expense2 = Expense.objects.create(date=datetime.date(2010, 2, 1),
                                               reference='BCDE',
                                               amount='200.0',
                                               payment_type=PAYMENT_TYPE_CASH,
                                               description='Second expense',
                                               owner_id=2)

    def testExpenseList(self):
        response = self.client.get(reverse('expense_list'))
        expense_list = response.context['expenses'].object_list.all()
        self.assertEquals(set(expense_list), set([self.expense1]))

    def testExpenseAdd(self):
        """
        Nothing to test for this
        """
        pass

    def testExpenseEdit(self):
        response = self.client.post(reverse('expense_edit') + '?id=%d' % (self.expense2.id),
                                    {'date': datetime.date(2010, 4, 1),
                                     'reference': 'DEFG',
                                     'amount': '400',
                                     'payment_type': PAYMENT_TYPE_CASH,
                                     'description': 'Edit payment'})
        self.assertEquals(response.status_code, 404)

    def testExpenseDelete(self):
        response = self.client.post(reverse('expense_delete'),
                                    {'id': self.expense2.id})
        self.assertEquals(response.status_code, 404)

class InvoicePermissionTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.proposal1 = Proposal.objects.create(project_id=30,
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_DRAFT,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=2005,
                                                owner_id=1)
        self.proposal2 = Proposal.objects.create(project_id=30,
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_DRAFT,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=2005,
                                                owner_id=2)
        self.invoice1 = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                               invoice_id=1,
                                               state=INVOICE_STATE_PAID,
                                               amount='100',
                                               edition_date=datetime.date(2010, 8, 31),
                                               payment_date=datetime.date(2010, 9, 30),
                                               paid_date=None,
                                               payment_type=PAYMENT_TYPE_CHECK,
                                               execution_begin_date=datetime.date(2010, 8, 1),
                                               execution_end_date=datetime.date(2010, 8, 7),
                                               penalty_date=datetime.date(2010, 10, 8),
                                               penalty_rate='1.5',
                                               discount_conditions='Nothing',
                                               owner_id=1)

        self.invoice1_row = InvoiceRow.objects.create(proposal_id=self.proposal1.id,
                                          invoice_id=self.invoice1.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='10',
                                          balance_payments=False,
                                          owner_id=1)

        self.invoice2 = Invoice.objects.create(customer_id=self.proposal2.project.customer_id,
                                               invoice_id=2,
                                               state=INVOICE_STATE_EDITED,
                                               amount='200',
                                               edition_date=datetime.date(2010, 8, 31),
                                               payment_date=datetime.date(2010, 9, 30),
                                               paid_date=None,
                                               payment_type=PAYMENT_TYPE_CHECK,
                                               execution_begin_date=datetime.date(2010, 8, 1),
                                               execution_end_date=datetime.date(2010, 8, 7),
                                               penalty_date=datetime.date(2010, 10, 8),
                                               penalty_rate='1.5',
                                               discount_conditions='Nothing',
                                               owner_id=2)

        self.invoice2_row = InvoiceRow.objects.create(proposal_id=self.proposal2.id,
                                          invoice_id=self.invoice2.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='20',
                                          balance_payments=False,
                                          owner_id=2)

    def testInvoiceList(self):
        response = self.client.get(reverse('invoice_list'))
        invoice_list = response.context['invoices'].all()
        self.assertEquals(set(invoice_list), set([self.invoice1]))

    def testInvoiceListExport(self):
        """
        not testable
        """
        pass

    def testInvoiceAdd(self):
        """
        nothing to test
        """
        pass

    def testInvoiceEdit(self):
        response = self.client.get(reverse('invoice_edit', kwargs={'id': self.invoice2.id}))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('invoice_edit', kwargs={'id': self.invoice2.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_SENT,
                                     'invoice-amount': 1500,
                                     'invoice-edition_date': '2010-8-30',
                                     'invoice-payment_date': '2010-9-29',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CASH,
                                     'invoice-execution_begin_date': '2010-8-2',
                                     'invoice-execution_end_date': '2010-8-8',
                                     'invoice-penalty_date': '2010-10-9',
                                     'invoice-penalty_rate': 2,
                                     'invoice-discount_conditions':'-50%',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 1,
                                     'invoice_rows-0-proposal': self.proposal2.id,
                                     'invoice_rows-0-ownedobject_ptr': self.invoice2_row.id,
                                     'invoice_rows-0-label': 'My product',
                                     'invoice_rows-0-balance_payments': True,
                                     'invoice_rows-0-category': ROW_CATEGORY_PRODUCT,
                                     'invoice_rows-0-quantity': 5,
                                     'invoice_rows-0-unit_price': 300 })

        self.assertEqual(response.status_code, 404)


    def testInvoiceDetail(self):
        response = self.client.get(reverse('invoice_detail', kwargs={'id': self.invoice2.id}))
        self.assertEqual(response.status_code, 404)

    def testInvoiceDelete(self):
        response = self.client.get(reverse('invoice_delete', kwargs={'id': self.invoice2.id}))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('invoice_delete', kwargs={'id': self.invoice2.id}))
        self.assertEqual(response.status_code, 404)

    def testInvoiceDownload(self):
        response = self.client.get(reverse('invoice_download', kwargs={'id': self.invoice2.id}))
        self.assertEqual(response.status_code, 404)

class InvoiceTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.proposal = Proposal.objects.create(project_id=30,
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_ACCEPTED,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=2005,
                                                owner_id=1)

    def testList(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.creation_date = datetime.date(2010, 1, 1)
        profile.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='100',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='10',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_EDITED,
                                    amount='200',
                                    edition_date=datetime.date(2010, 8, 31),
                                    payment_date=datetime.date(2010, 9, 30),
                                    paid_date=None,
                                    payment_type=PAYMENT_TYPE_CHECK,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)

        i2_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i2.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='20',
                                          balance_payments=False,
                                          owner_id=1)

        invoices = [i, i2]

        response = self.client.get(reverse('invoice_list'))
        invoice_list = response.context['invoices'].all()
        self.assertEquals(set(invoice_list), set(invoices))

    def testGetAdd(self):
        """
        Tests getting Add invoice page
        """
        response = self.client.get(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer_id}))
        self.assertEqual(response.status_code, 200)

    def testPostAdd(self):
        """
        Tests posting to Add invoice page
        """
        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        self.assertEqual(response.status_code, 302)
        result = Invoice.objects.filter(customer__id=self.proposal.project.customer.id,
                                        invoice_id=1,
                                        state=INVOICE_STATE_EDITED,
                                        amount='1000',
                                        edition_date=datetime.date(2010, 8, 31),
                                        payment_date=datetime.date(2010, 9, 30),
                                        paid_date=None,
                                        payment_type=PAYMENT_TYPE_CHECK,
                                        execution_begin_date=datetime.date(2010, 8, 1),
                                        execution_end_date=datetime.date(2010, 8, 7),
                                        penalty_date=datetime.date(2010, 10, 8),
                                        penalty_rate='1.5',
                                        discount_conditions='Nothing',
                                        owner__id=1)
        self.assertEqual(len(result), 1)
        invoice_rows = result[0].invoice_rows.all()
        self.assertEqual(len(invoice_rows), 1)
        invoice_rows = result[0].invoice_rows.filter(label='Day of work',
                                                     proposal__id=self.proposal.id,
                                                     balance_payments=False,
                                                     category=ROW_CATEGORY_SERVICE,
                                                     quantity=10,
                                                     unit_price='100')
        self.assertEqual(len(invoice_rows), 1)

    def testGetEdit(self):
        """
        Tests getting Edit invoice page
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('invoice_edit', kwargs={'id': i.id}))
        self.assertEqual(response.status_code, 200)

    def testPostEdit(self):
        """
        Tests posting to Edit invoice page
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.post(reverse('invoice_edit', kwargs={'id': i.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_SENT,
                                     'invoice-amount': 1500,
                                     'invoice-edition_date': '2010-8-30',
                                     'invoice-payment_date': '2010-9-29',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CASH,
                                     'invoice-execution_begin_date': '2010-8-2',
                                     'invoice-execution_end_date': '2010-8-8',
                                     'invoice-penalty_date': '2010-10-9',
                                     'invoice-penalty_rate': 2,
                                     'invoice-discount_conditions':'-50%',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 1,
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-ownedobject_ptr': i_row.id,
                                     'invoice_rows-0-label': 'My product',
                                     'invoice_rows-0-balance_payments': True,
                                     'invoice_rows-0-category': ROW_CATEGORY_PRODUCT,
                                     'invoice_rows-0-quantity': 5,
                                     'invoice_rows-0-unit_price': 300 })

        self.assertEqual(response.status_code, 302)
        result = Invoice.objects.filter(id=i.id,
                                        customer__id=self.proposal.project.customer.id,
                                        invoice_id=1,
                                        state=INVOICE_STATE_SENT,
                                        amount='1500',
                                        edition_date=datetime.date(2010, 8, 30),
                                        payment_date=datetime.date(2010, 9, 29),
                                        paid_date=None,
                                        payment_type=PAYMENT_TYPE_CASH,
                                        execution_begin_date=datetime.date(2010, 8, 2),
                                        execution_end_date=datetime.date(2010, 8, 8),
                                        penalty_date=datetime.date(2010, 10, 9),
                                        penalty_rate='2',
                                        discount_conditions='-50%',
                                        owner__id=1)

        self.assertEqual(len(result), 1)
        invoice_rows = result[0].invoice_rows.all()
        self.assertEqual(len(invoice_rows), 1)
        invoice_rows = result[0].invoice_rows.filter(proposal__id=self.proposal.id,
                                                     label='My product',
                                                     balance_payments=True,
                                                     category=ROW_CATEGORY_PRODUCT,
                                                     quantity=5,
                                                     unit_price='300')
        self.assertEqual(len(invoice_rows), 1)

    def testGetDelete(self):
        """
        Tests getting Delete invoice page
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('invoice_delete', kwargs={'id': i.id}))
        self.assertEqual(response.status_code, 200)

    def testPostDelete(self):
        """
        Tests posting to Delete invoice page
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.post(reverse('invoice_delete', kwargs={'id': i.id}),
                                    {'delete': 'Ok'})
        self.assertEqual(response.status_code, 302)
        result = Invoice.objects.all()
        self.assertEqual(len(result), 0)
        result = InvoiceRow.objects.all()
        self.assertEqual(len(result), 0)

    def testGetDetail(self):
        """
        Tests getting Detail invoice page
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('invoice_detail', kwargs={'id': i.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['invoice'], i)

    def testAmountLTEProposal(self):
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_EDITED,
                                    edition_date=datetime.date(2010, 8, 31),
                                    payment_date=datetime.date(2010, 9, 30),
                                    paid_date=None,
                                    payment_type=PAYMENT_TYPE_CHECK,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)

        i2_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                           invoice_id=i2.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=10,
                                           unit_price='100.5',
                                           balance_payments=False,
                                           owner_id=1)

        user = User.objects.get(pk=1)
        i2_row.unit_price = 100.6
        self.assertRaises(InvoiceRowAmountError, i2_row.save, user=user)

        response = self.client.post(reverse('invoice_edit', kwargs={'id': i.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_SENT,
                                     'invoice-edition_date': '2010-8-30',
                                     'invoice-payment_date': '2010-9-29',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-2',
                                     'invoice-execution_end_date': '2010-8-8',
                                     'invoice-penalty_date': '2010-10-9',
                                     'invoice-penalty_rate': 2,
                                     'invoice-discount_conditions':'-50%',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 1,
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-ownedobject_ptr': i_row.id,
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-balance_payments': True,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100.6 })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amount invoiced for proposal can&#39;t be greater than proposal amount")

    def testInvoiceIdIsUnique(self):
        """
        Tests that each invoice_id is unique for a user
        """
        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        self.assertEqual(response.status_code, 200)
        self.assertTrue('invoice_id' in response.context['invoiceForm'].errors)

        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer.id}),
                                    {'invoice-invoice_id': 2,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        invoice = Invoice.objects.get(invoice_id=2)
        response = self.client.post(reverse('invoice_edit', kwargs={'id': invoice.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        self.assertEqual(response.status_code, 200)
        self.assertTrue('invoice_id' in response.context['invoiceForm'].errors)

    def testDownloadPdf(self):
        """
        Tests non-regression on pdf
        """
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('invoice_download', kwargs={'id': i.id}))
        self.assertEqual(response.status_code, 200)
        f = open('/tmp/invoice.pdf', 'w')
        f.write(response.content)
        f.close()
        content = response.content.split("\n")
        invariant_content = content[0:66] + content[67:109] + content[110:-1]
        self.assertEquals(hashlib.md5("\n".join(invariant_content)).hexdigest(),
                          "39f85a7a13ffd31caa800e5e2b2cf6db")

    def testInvoiceBookDownloadPdf(self):
        """
        Tests non-regression on pdf
        """
        for i in range(1, 50):
            invoice = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=i,
                                   state=INVOICE_STATE_PAID,
                                   amount='1',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

            i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=invoice.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='1',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('invoice_list_export') + '?year=%(year)s' % {'year': '2010'})
        self.assertEqual(response.status_code, 200)
        f = open('/tmp/invoice_book.pdf', 'w')
        f.write(response.content)
        f.close()
        content = response.content.split("\n")
        invariant_content = content[0:85] + content[86:140] + content[141:-1]
        self.assertEquals(hashlib.md5("\n".join(invariant_content)).hexdigest(),
                          "80d1843fa31563356782e54df6c42b8f")

    def testBalancePayment(self):
        """
        Tests changing state of proposal to balanced
        """
        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': self.proposal.project.customer.id}),
                                    {'invoice-invoice_id': 1,
                                     'invoice-state': INVOICE_STATE_PAID,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '2010-10-30',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': self.proposal.id,
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100,
                                     'invoice_rows-0-balance_payments': True })

        self.assertEquals(response.status_code, 302)
        proposal = Proposal.objects.get(pk=self.proposal.id)
        self.assertEquals(proposal.state, PROPOSAL_STATE_BALANCED)
        self.assertEquals(proposal.get_remaining_to_invoice(), 0)

class ExpenseTest(TestCase):
    fixtures = ['test_users', ]

    def setUp(self):
        self.client.login(username='test', password='test')

    def testList(self):
        expense1 = Expense.objects.create(date=datetime.date(2010, 1, 1),
                                          reference='ABCD',
                                          amount='100.0',
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          description='First expense',
                                          owner_id=1)
        expense2 = Expense.objects.create(date=datetime.date(2010, 2, 1),
                                          reference='BCDE',
                                          amount='200.0',
                                          payment_type=PAYMENT_TYPE_CASH,
                                          description='Second expense',
                                          owner_id=1)
        expense3 = Expense.objects.create(date=datetime.date(2010, 3, 1),
                                          reference='CDEF',
                                          amount='300.0',
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          description='Third expense',
                                          owner_id=1)

        expenses = [expense1, expense2, expense3]

        response = self.client.get(reverse('expense_list'))
        expense_list = response.context['expenses'].object_list.all()
        self.assertEquals(set(expense_list), set(expenses))

    def testPostAdd(self):
        response = self.client.post(reverse('expense_add'),
                                    {'date': datetime.date(2010, 4, 1),
                                     'reference': 'DEFG',
                                     'amount': '400',
                                     'payment_type': PAYMENT_TYPE_CASH,
                                     'description': 'Add payment'})

        result = Expense.objects.filter(date=datetime.date(2010, 4, 1),
                                        reference='DEFG',
                                        amount='400.0',
                                        payment_type=PAYMENT_TYPE_CASH,
                                        description='Add payment',
                                        owner__id=1)
        self.assertEqual(len(result), 1)
        json_response = simplejson.loads(response.content)
        self.assertEquals(json_response, {u'date': localize(datetime.date(2010, 4, 1)),
                                          u'reference': 'DEFG',
                                          u'amount': '400',
                                          u'payment_type': PAYMENT_TYPE_CASH,
                                          u'payment_type_label': 'Cash',
                                          u'description': 'Add payment',
                                          u'id': result[0].id,
                                          u'error': 'ok'})

    def testPostEdit(self):
        expense1 = Expense.objects.create(date=datetime.date(2010, 1, 1),
                                          reference='ABCD',
                                          amount='100.0',
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          description='First expense',
                                          owner_id=1)
        response = self.client.post(reverse('expense_edit') + '?id=%d' % (expense1.id),
                                    {'date': datetime.date(2010, 4, 1),
                                     'reference': 'DEFG',
                                     'amount': '400',
                                     'payment_type': PAYMENT_TYPE_CASH,
                                     'description': 'Edit payment'})

        result = Expense.objects.filter(date=datetime.date(2010, 4, 1),
                                        reference='DEFG',
                                        amount='400.0',
                                        payment_type=PAYMENT_TYPE_CASH,
                                        description='Edit payment',
                                        owner__id=1)
        self.assertEqual(len(result), 1)
        json_response = simplejson.loads(response.content)
        self.assertEquals(json_response, {u'date': localize(datetime.date(2010, 4, 1)),
                                          u'reference': 'DEFG',
                                          u'amount': '400',
                                          u'payment_type': PAYMENT_TYPE_CASH,
                                          u'payment_type_label': 'Cash',
                                          u'description': 'Edit payment',
                                          u'id': expense1.id,
                                          u'error': 'ok'})

    def testPostDelete(self):
        expense1 = Expense.objects.create(date=datetime.date(2010, 1, 1),
                                          reference='ABCD',
                                          amount='100.0',
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          description='First expense',
                                          owner_id=1)
        response = self.client.post(reverse('expense_delete'),
                                    {'id': expense1.id})

        result = Expense.objects.all()
        self.assertEqual(len(result), 0)
        json_response = simplejson.loads(response.content)
        self.assertEquals(json_response, {u'id': expense1.id,
                                          u'error': 'ok'})
