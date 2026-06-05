import { isAxiosError } from 'axios';
import { Anchor, Button, Container, Divider, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { Link } from 'react-router';
import logoTitle from '../../assets/logo/gamerec-logo-title-transparent.png';
import { useAuth } from '../../hooks/useAuth';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';
import classes from './AuthPages.module.css';

export default function RegisterPage() {
  const { register, loginWithGoogle } = useAuth();

  const form = useForm({
    initialValues: { email: '', display_name: '', password: '' },
    validate: {
      email:        (v) => (/^\S+@\S+$/.test(v) ? null : 'Invalid email'),
      display_name: (v) => (v.length >= 2 ? null : 'Display name too short'),
      password:     (v) => (v.length >= 8 ? null : 'Password must be at least 8 characters'),
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    try {
      await register(values);
    } catch (err: unknown) {
      const message = isAxiosError(err) ? (err.response?.data?.detail ?? 'Registration failed') : 'Registration failed';
      notifications.show({ color: 'red', title: 'Error', message });
    }
  });

  return (
    <div className={classes.page}>
      <Container size={440} className={classes.shell}>
        <div className={classes.brand}>
          <img src={logoTitle} alt="GameRec" className={classes.brandLogo} />
        </div>
        <Title ta="center" className={classes.title}>Create an account</Title>
        <Text c="dimmed" size="sm" ta="center" mt={6} className={classes.subtitle}>
          Start a personal game library that can explain what fits your taste.
        </Text>
        <Text c="dimmed" size="sm" ta="center" mt={8}>
          Already have an account?{' '}
          <Anchor component={Link} to="/login" c="ember.3">
            Sign in
          </Anchor>
        </Text>

      <Paper withBorder p="xl" mt="lg" radius="md" className={classes.card}>
        <GoogleSignInButton
          fullWidth
          label="Sign up with Google"
          onSuccess={(accessToken) =>
            loginWithGoogle(accessToken).catch(() =>
              notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or register with email' })
            )
          }
          onError={() =>
            notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or register with email' })
          }
        />

        {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
          <Divider label="or register with email" labelPosition="center" my="md" />
        )}

        <form onSubmit={handleSubmit}>
          <TextInput
            className={classes.input}
            label="Display name"
            placeholder="Your name"
            required
            {...form.getInputProps('display_name')}
          />
          <TextInput
            className={classes.input}
            label="Email"
            placeholder="you@example.com"
            required
            mt="md"
            {...form.getInputProps('email')}
          />
          <PasswordInput
            className={classes.input}
            label="Password"
            placeholder="At least 8 characters"
            required
            mt="md"
            {...form.getInputProps('password')}
          />

          <Button type="submit" fullWidth mt="xl">
            Register
          </Button>
        </form>
      </Paper>
    </Container>
    </div>
  );
}
