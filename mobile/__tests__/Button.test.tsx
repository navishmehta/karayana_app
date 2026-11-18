import { fireEvent, render, screen } from '@testing-library/react-native';

import { Button } from '@/components/ui/Button';
import { ThemeProvider } from '@/theme/ThemeProvider';

const renderButton = (props: Partial<React.ComponentProps<typeof Button>> = {}) => {
  const onPress = jest.fn();
  return {
    onPress,
    view: render(
      <ThemeProvider>
        <Button title="Save" onPress={onPress} {...props} />
      </ThemeProvider>,
    ),
  };
};

it('shows its title and responds to taps', async () => {
  const { onPress, view } = renderButton();
  await view;
  await fireEvent.press(screen.getByRole('button'));
  expect(screen.getByText('Save')).toBeTruthy();
  expect(onPress).toHaveBeenCalledTimes(1);
});

it('ignores taps and reports busy while loading', async () => {
  const { onPress, view } = renderButton({ loading: true });
  await view;
  const button = screen.getByRole('button');
  await fireEvent.press(button);
  expect(onPress).not.toHaveBeenCalled();
  expect(button.props.accessibilityState).toMatchObject({ disabled: true, busy: true });
});
