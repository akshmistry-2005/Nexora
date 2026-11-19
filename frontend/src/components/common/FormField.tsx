import React, {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react';

export interface BaseFieldProps {
  label?: string;
  error?: string | null;
  helperText?: string;
  required?: boolean;
  style?: React.CSSProperties;
}

export interface InputFieldProps extends BaseFieldProps, InputHTMLAttributes<HTMLInputElement> {
  fieldType?: 'input';
}

export interface SelectFieldProps extends BaseFieldProps, SelectHTMLAttributes<HTMLSelectElement> {
  fieldType: 'select';
  options: { label: string; value: string | number }[];
}

export interface TextareaFieldProps
  extends BaseFieldProps, TextareaHTMLAttributes<HTMLTextAreaElement> {
  fieldType: 'textarea';
}

export type FormFieldProps = InputFieldProps | SelectFieldProps | TextareaFieldProps;

export const FormField: React.FC<FormFieldProps> = (props) => {
  const { label, error, helperText, required, style = {}, id, ...rest } = props;
  const fieldId = id || (label ? `field-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

  const renderControl = (): ReactNode => {
    const commonStyles: React.CSSProperties = {
      width: '100%',
      background: 'var(--color-bg-surface-elevated)',
      border: `1px solid ${error ? 'var(--color-danger)' : 'var(--color-border-default)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '0.5rem 0.75rem',
      color: 'var(--color-text-primary)',
      fontSize: '0.875rem',
      transition: 'border-color var(--transition-fast)',
      boxSizing: 'border-box',
    };

    if (props.fieldType === 'select') {
      const { options, ...selectProps } = props as SelectFieldProps;
      return (
        <select
          id={fieldId}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error ? `${fieldId}-error` : helperText ? `${fieldId}-helper` : undefined
          }
          style={commonStyles}
          {...selectProps}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );
    }

    if (props.fieldType === 'textarea') {
      const textareaProps = rest as TextareaHTMLAttributes<HTMLTextAreaElement>;
      return (
        <textarea
          id={fieldId}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error ? `${fieldId}-error` : helperText ? `${fieldId}-helper` : undefined
          }
          style={{ ...commonStyles, minHeight: '80px', resize: 'vertical' }}
          {...textareaProps}
        />
      );
    }

    const inputProps = rest as InputHTMLAttributes<HTMLInputElement>;
    return (
      <input
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${fieldId}-error` : helperText ? `${fieldId}-helper` : undefined}
        style={commonStyles}
        {...inputProps}
      />
    );
  };

  return (
    <div style={{ marginBottom: '1rem', ...style }}>
      {label && (
        <label
          htmlFor={fieldId}
          style={{
            display: 'block',
            marginBottom: '0.35rem',
            fontSize: '0.8125rem',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
          }}
        >
          {label}
          {required && <span style={{ color: 'var(--color-danger)', marginLeft: '3px' }}>*</span>}
        </label>
      )}

      {renderControl()}

      {error ? (
        <div
          id={`${fieldId}-error`}
          role="alert"
          data-testid="field-error"
          style={{
            color: 'var(--color-danger)',
            fontSize: '0.75rem',
            marginTop: '0.3rem',
            fontWeight: 500,
          }}
        >
          {error}
        </div>
      ) : helperText ? (
        <div
          id={`${fieldId}-helper`}
          style={{
            color: 'var(--color-text-muted)',
            fontSize: '0.75rem',
            marginTop: '0.3rem',
          }}
        >
          {helperText}
        </div>
      ) : null}
    </div>
  );
};
