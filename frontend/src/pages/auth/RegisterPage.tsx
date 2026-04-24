import { isAxiosError } from 'axios';
import { Anchor, Button, Container, Divider, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { GoogleLogin } from '@react-oauth/google';
import { Link } from 'react-router';
import { useAuth } from '../../hooks/useAuth';

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
    <Container size={420} my={40}>
      <Title ta="center">Create an account</Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Already have an account?{' '}
        <Anchor component={Link} to="/login">
          Sign in
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <GoogleLogin
          onSuccess={(cred: { credential?: string }) => {
            if (cred.credential) loginWithGoogle(cred.credential).catch(() => {
              notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or register with email' });
            });
          }}
          onError={() =>
            notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or register with email' })
          }
          width="100%"
          text="signup_with"
        />

        <Divider label="or register with email" labelPosition="center" my="md" />

        <form onSubmit={handleSubmit}>
          <TextInput
            label="Display name"
            placeholder="Your name"
            required
            {...form.getInputProps('display_name')}
          />
          <TextInput
            label="Email"
            placeholder="you@example.com"
            required
            mt="md"
            {...form.getInputProps('email')}
          />
          <PasswordInput
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
  );
}
