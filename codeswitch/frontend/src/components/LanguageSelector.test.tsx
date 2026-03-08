import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import LanguageSelector from '../components/LanguageSelector';

describe('LanguageSelector', () => {
  const languages = ['python', 'java', 'javascript', 'c', 'cpp'];

  it('renders all language options', () => {
    render(
      <LanguageSelector
        value="python"
        onChange={() => { }}
        languages={languages}
      />
    );
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    // One option per language
    expect(screen.getAllByRole('option')).toHaveLength(languages.length);
  });

  it('renders label when provided', () => {
    render(
      <LanguageSelector
        value="python"
        onChange={() => { }}
        languages={languages}
        label="Source"
      />
    );
    expect(screen.getByText('Source')).toBeInTheDocument();
  });

  it('shows current value as selected', () => {
    render(
      <LanguageSelector
        value="java"
        onChange={() => { }}
        languages={languages}
      />
    );
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('java');
  });

  it('calls onChange with new value when user selects', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(
      <LanguageSelector
        value="python"
        onChange={handleChange}
        languages={languages}
      />
    );
    await user.selectOptions(screen.getByRole('combobox'), 'java');
    expect(handleChange).toHaveBeenCalledWith('java');
  });

  it('displays human-readable label for known language', () => {
    render(
      <LanguageSelector
        value="python"
        onChange={() => { }}
        languages={['python']}
      />
    );
    expect(screen.getByRole('option', { name: 'Python' })).toBeInTheDocument();
  });
});
