import { Anchor, Button, Container, Divider, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { Link } from 'react-router';
import { useAuth } from '../../hooks/useAuth';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';

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
    <Container size={420} my={40}>
      <Title ta="center">Welcome back</Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Don't have an account?{' '}
        <Anchor component={Link} to="/register">
          Register
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
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
            label="Email"
            placeholder="you@example.com"
            required
            {...form.getInputProps('email')}
          />
          <PasswordInput
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
  );
}
