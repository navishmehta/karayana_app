/** Client-side checks for staff forms (the server re-checks everything and its messages win). */
import type { TFunction } from 'i18next';
import { z } from 'zod';

import { isValidDisplayDate } from '@/utils/dates';

const MONEY = /^\d{1,7}(\.\d{1,2})?$/;
const QUANTITY = /^\d{1,6}(\.\d{1,3})?$/;

export const requiredText = (t: TFunction) => z.string().trim().min(1, t('validation.required'));
export const optionalText = () => z.string();
export const money = (t: TFunction) => z.string().trim().regex(MONEY, t('staff.validation.money'));
export const optionalMoney = (t: TFunction) => z.string().trim().refine((v) => !v || MONEY.test(v), t('staff.validation.money'));
export const quantity = (t: TFunction) => z.string().trim().regex(QUANTITY, t('staff.validation.quantity'));
export const optionalQuantity = (t: TFunction) =>
  z.string().trim().refine((v) => !v || QUANTITY.test(v), t('staff.validation.quantity'));
export const positiveQuantity = (t: TFunction) =>
  quantity(t).refine((v) => Number(v) > 0, t('staff.validation.positive'));
export const optionalDate = (t: TFunction) =>
  z.string().trim().refine((v) => !v || isValidDisplayDate(v), t('staff.validation.date'));
export const requiredId = (t: TFunction) => z.number({ message: t('validation.required') }).int().positive(t('validation.required'));
