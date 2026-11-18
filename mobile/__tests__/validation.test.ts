import i18n from '@/i18n';
import { loginSchema, resetSchema } from '@/lib/validation';

const t = i18n.t.bind(i18n);

describe('form validation', () => {
  beforeAll(() => i18n.changeLanguage('en'));

  it('checks the login form', () => {
    const result = loginSchema(t).safeParse({ email: 'not-an-email', password: '' });
    expect(result.success).toBe(false);
    const messages = result.error?.issues.map((i) => i.message);
    expect(messages).toEqual(['Enter a valid email address.', 'This field is required.']);
  });

  it('checks the reset form: code length, password strength and confirmation', () => {
    const schema = resetSchema(t);
    expect(schema.safeParse({ code: '123456', password: 'Strong123', confirm: 'Strong123' }).success).toBe(true);
    const bad = schema.safeParse({ code: '12', password: 'weakpassword', confirm: 'other' });
    expect(bad.error?.issues.map((i) => i.path[0])).toEqual(['code', 'password', 'confirm']);
  });

  it('translates messages to Punjabi', async () => {
    await i18n.changeLanguage('pa');
    const result = loginSchema(t).safeParse({ email: '', password: '' });
    expect(result.error?.issues[0].message).toBe('ਇਹ ਖੇਤਰ ਭਰਨਾ ਲਾਜ਼ਮੀ ਹੈ।');
    await i18n.changeLanguage('en');
  });
});
