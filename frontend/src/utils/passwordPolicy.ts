const MIN_PASSWORD_LENGTH = 8;

const PASSWORD_POLICY_MESSAGE =
  'Password must be at least 8 characters, include at least 3 of lowercase letters, uppercase letters, numbers, and symbols, and not include your email or display name.';

type PasswordPolicyContext = {
  email?: string;
  displayName?: string;
};

type PasswordRequirement = {
  id: string;
  label: string;
  met: boolean;
};

function compact(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function getDisplayNameTokens(displayName?: string) {
  return displayName?.toLowerCase().match(/[a-z0-9]+/g)?.filter((token) => token.length >= 3) ?? [];
}

export function getPasswordRequirements(password: string, context: PasswordPolicyContext = {}): PasswordRequirement[] {
  const compactPassword = compact(password);
  const emailLocalPart = context.email ? compact(context.email.split('@')[0]) : '';
  const displayNameTokens = getDisplayNameTokens(context.displayName);
  const hasPassword = password.length > 0;
  const classCount = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length;

  return [
    {
      id:    'length',
      label: '8 or more characters',
      met:   password.length >= MIN_PASSWORD_LENGTH,
    },
    {
      id:    'character-mix',
      label: 'At least 3 types: lowercase, uppercase, number, symbol',
      met:   classCount >= 3,
    },
    {
      id:    'email',
      label: 'Does not include your email',
      met:   hasPassword && !(emailLocalPart.length >= 3 && compactPassword.includes(emailLocalPart)),
    },
    {
      id:    'display-name',
      label: 'Does not include your display name',
      met:   hasPassword && !displayNameTokens.some((token) => compactPassword.includes(token)),
    },
  ];
}

export function validatePasswordPolicy(password: string, context: PasswordPolicyContext = {}) {
  if (!password.trim()) {
    return 'Password cannot be empty.';
  }

  if (password.length < MIN_PASSWORD_LENGTH) {
    return PASSWORD_POLICY_MESSAGE;
  }

  const requirements = getPasswordRequirements(password, context);
  if (!requirements.every((requirement) => requirement.met)) {
    return PASSWORD_POLICY_MESSAGE;
  }

  return null;
}
