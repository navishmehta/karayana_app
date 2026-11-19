import mockAsyncStorage from '@react-native-async-storage/async-storage/jest/async-storage-mock';

jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);

// Animations are skipped in tests. A small stand-in for the parts of Reanimated the app uses
// (the library's own mock needs native modules that Jest doesn't have).
jest.mock('react-native-reanimated', () => {
  const { View } = jest.requireActual('react-native');
  const builder: Record<string, unknown> = {};
  for (const step of ['delay', 'springify', 'damping', 'duration']) builder[step] = () => builder;
  const shared = (initial: unknown) => {
    let value = initial;
    return { value, get: () => value, set: (next: unknown) => (value = next) };
  };
  const Animated = { View, createAnimatedComponent: (component: unknown) => component };
  return {
    __esModule: true,
    default: Animated,
    ...Animated,
    useSharedValue: shared,
    useAnimatedStyle: (style: () => object) => style(),
    withSpring: (to: unknown) => to,
    withTiming: (to: unknown) => to,
    withRepeat: (animation: unknown) => animation,
    FadeInDown: builder,
  };
});
