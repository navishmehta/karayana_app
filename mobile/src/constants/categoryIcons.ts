/**
 * Icons for categories that have no photo yet. Matched on words in the category's English name, so admin-created
 * categories get a sensible icon too. Add a line here to support a new kind of category.
 */
import type Ionicons from '@expo/vector-icons/Ionicons';

type IconName = keyof typeof Ionicons.glyphMap;

export const CATEGORY_ICON_RULES: readonly { words: readonly string[]; icon: IconName }[] = [
  { words: ['dairy', 'milk', 'paneer', 'curd'], icon: 'water' },
  { words: ['grocery', 'grain', 'rice', 'atta', 'flour', 'dal', 'pulse', 'staple'], icon: 'basket' },
  { words: ['snack', 'namkeen', 'chips', 'biscuit'], icon: 'fast-food' },
  { words: ['drink', 'beverage', 'juice', 'soda'], icon: 'beer' },
  { words: ['tea', 'coffee'], icon: 'cafe' },
  { words: ['personal', 'care', 'beauty', 'soap', 'shampoo'], icon: 'body' },
  { words: ['household', 'home', 'kitchen'], icon: 'home' },
  { words: ['bakery', 'bread', 'cake'], icon: 'pizza' },
  { words: ['spice', 'masala'], icon: 'flame' },
  { words: ['clean', 'detergent', 'wash'], icon: 'sparkles' },
  { words: ['stationery', 'stationary', 'pen', 'book'], icon: 'pencil' },
  { words: ['fruit', 'vegetable', 'fresh', 'organic'], icon: 'leaf' },
  { words: ['egg'], icon: 'egg' },
  { words: ['frozen', 'ice cream'], icon: 'ice-cream' },
  { words: ['medicine', 'health', 'pharma'], icon: 'medkit' },
  { words: ['pet'], icon: 'paw' },
];

export const DEFAULT_CATEGORY_ICON: IconName = 'pricetag';
