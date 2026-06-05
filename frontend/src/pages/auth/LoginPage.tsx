import { Anchor, Button, Container, Divider, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { Link } from 'react-router';
import logoTitle from '../../assets/logo/gamerec-logo-title-transparent.png';
import { useAuth } from '../../hooks/useAuth';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';
import classes from './AuthPages.module.css';

export default function LoginPage() {
  const { login, loginWithGoogle } = useAuth();

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email:    (v) => (/^\S+@\S+$/.test(v) ? null : 'Invalid email'),
      password: (v) => (v.length >= 8 ? null : 'Password must be at least 8 characters'),
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    try {
      await login({ username: values.email, password: values.password });
    } catch {
      notifications.show({ color: 'red', title: 'Login failed', message: 'Invalid email or password' });
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

      <Paper withBorder p="xl" mt="lg" radius="md" className={classes.card}>
        <GoogleSignInButton
          fullWidth
          onSuccess={(accessToken) =>
            loginWithGoogle(accessToken).catch(() =>
              notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or use email/password' })
            )
          }
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
            {...form.getInputProps('email')}
          />
          <PasswordInput
            className={classes.input}
            label="Password"
            placeholder="Your password"
            required
            mt="md"
            {...form.getInputProps('password')}
          />

          {/* TODO: Add Anchor to /password-reset for stretch goal */}

          <Button type="submit" fullWidth mt="xl">
            Sign in
          </Button>
        </form>
      </Paper>
    </Container>
    </div>
  );
}
