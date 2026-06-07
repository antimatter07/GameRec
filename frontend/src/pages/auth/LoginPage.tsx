import { Anchor, Button, Container, Divider, Paper, PasswordInput, Progress, Text, TextInput, ThemeIcon, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { Link } from 'react-router';
import { useState } from 'react';
import { IconLogin2 } from '@tabler/icons-react';
import logoTitle from '../../assets/logo/gamerec-logo-title-transparent.png';
import { useAuth } from '../../hooks/useAuth';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';
import classes from './AuthPages.module.css';

export default function LoginPage() {
  const { login, loginWithGoogle } = useAuth();
  const [isEmailSubmitting, setIsEmailSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);
  const isProcessing = isEmailSubmitting || isGoogleSubmitting;

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email:    (v) => (/^\S+@\S+$/.test(v) ? null : 'Invalid email'),
      password: (v) => (v.length >= 8 ? null : 'Password must be at least 8 characters'),
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    try {
      setIsEmailSubmitting(true);
      await login({ username: values.email, password: values.password });
    } catch {
      notifications.show({ color: 'red', title: 'Login failed', message: 'Invalid email or password' });
    } finally {
      setIsEmailSubmitting(false);
    }
  });

  return (
    <div className={classes.page}>
      <Container size={440} className={classes.shell}>
        <div className={classes.brand}>
          <img src={logoTitle} alt="GameRec" className={classes.brandLogo} />
        </div>
        <Title ta="center" className={classes.title}>Welcome back</Title>
        <Text c="dimmed" size="sm" ta="center" mt={6} className={classes.subtitle}>
          Sign in to continue shaping your library, queue, and recommendations.
        </Text>
        <Text c="dimmed" size="sm" ta="center" mt={8}>
          Need an account?{' '}
          <Anchor component={Link} to="/register" c="ember.3">
            Create one
          </Anchor>
        </Text>

      <Paper withBorder p="xl" mt="lg" radius="xs" className={classes.card}>
        <GoogleSignInButton
          fullWidth
          loading={isGoogleSubmitting}
          disabled={isProcessing}
          label={isGoogleSubmitting ? 'Finishing Google sign-in...' : 'Continue with Google'}
          onSuccess={async (accessToken) => {
            try {
              setIsGoogleSubmitting(true);
              await loginWithGoogle(accessToken);
            } catch {
              notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or use email/password' });
            } finally {
              setIsGoogleSubmitting(false);
            }
          }}
          onError={() =>
            notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or use email/password' })
          }
        />

        {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
          <Divider label="or sign in with email" labelPosition="center" my="md" />
        )}

        <form onSubmit={handleSubmit}>
          <TextInput
            className={classes.input}
            label="Email"
            placeholder="you@example.com"
            required
            disabled={isProcessing}
            {...form.getInputProps('email')}
          />
          <PasswordInput
            className={classes.input}
            label="Password"
            placeholder="Your password"
            required
            mt="md"
            disabled={isProcessing}
            {...form.getInputProps('password')}
          />

          {/* TODO: Add Anchor to /password-reset for stretch goal */}

          {isProcessing && (
            <div className={classes.processingPanel} role="status" aria-live="polite" aria-atomic="true">
              <ThemeIcon radius="sm" color="ember" variant="light" size={34}>
                <IconLogin2 size={18} />
              </ThemeIcon>
              <div className={classes.processingContent}>
                <Text size="sm" fw={600}>
                  {isGoogleSubmitting ? 'Finishing Google sign-in' : 'Signing you in'}
                </Text>
                <Text size="xs" c="dimmed">
                  We are verifying your account and loading your GameRec session.
                </Text>
                <Progress value={72} color="ember" radius="xs" size="xs" mt={8} aria-label="Sign-in processing" />
              </div>
            </div>
          )}

          <Button type="submit" fullWidth mt="xl" loading={isEmailSubmitting} disabled={isProcessing}>
            {isEmailSubmitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </Paper>
    </Container>
    </div>
  );
}
