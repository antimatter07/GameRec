import { Button, type ButtonProps } from '@mantine/core';
import { IconBrandGoogle } from '@tabler/icons-react';
import { useGoogleLogin } from '@react-oauth/google';

interface GoogleSignInButtonProps extends Omit<ButtonProps, 'onClick' | 'leftSection'> {
  onSuccess: (accessToken: string) => void;
  onError?: () => void;
  label?: string;
}

function GoogleSignInButtonInner({
  onSuccess,
  onError,
  label = 'Continue with Google',
  ...buttonProps
}: GoogleSignInButtonProps) {
  const triggerGoogleLogin = useGoogleLogin({
    onSuccess: (response) => onSuccess(response.access_token),
    onError: onError,
    scope: 'openid email profile',
  });

  return (
    <Button
      variant="outline"
      leftSection={<IconBrandGoogle size={18} />}
      onClick={() => triggerGoogleLogin()}
      {...buttonProps}
    >
      {label}
    </Button>
  );
}

export function GoogleSignInButton(props: GoogleSignInButtonProps) {
  // Only render when GoogleOAuthProvider is active (client ID configured)
  if (!import.meta.env.VITE_GOOGLE_CLIENT_ID) return null;
  return <GoogleSignInButtonInner {...props} />;
}
