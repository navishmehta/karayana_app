/** A TextField wired to react-hook-form, so long forms stay short. */
import { type Control, Controller, type FieldValues, type Path } from 'react-hook-form';

import { TextField, type TextFieldProps } from '@/components/ui/TextField';

export function FormText<T extends FieldValues>({
  control,
  name,
  ...props
}: { control: Control<T>; name: Path<T> } & Omit<TextFieldProps, 'value' | 'onChangeText'>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <TextField
          {...props}
          value={field.value == null ? '' : String(field.value)}
          onChangeText={field.onChange}
          onBlur={field.onBlur}
          error={fieldState.error?.message}
        />
      )}
    />
  );
}
