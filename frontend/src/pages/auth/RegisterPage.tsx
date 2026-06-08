import { isAxiosError } from 'axios';
import { Anchor, Button, Container, Divider, Paper, PasswordInput, Progress, Text, TextInput, ThemeIcon, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { Link } from 'react-router';
import { useState } from 'react';
import { IconCheck, IconUserPlus } from '@tabler/icons-react';
import logoTitle from '../../assets/logo/gamerec-logo-title-transparent.png';
import { useAuth } from '../../hooks/useAuth';
import { GoogleSignInButton } from '../../components/GoogleSignInButton';
import { getPasswordRequirements, validatePasswordPolicy } from '../../utils/passwordPolicy';
import classes from './AuthPages.module.css';

export default function RegisterPage() {
  const { register, loginWithGoogle } = useAuth();
  const [isEmailSubmitting, setIsEmailSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);
  const isProcessing = isEmailSubmitting || isGoogleSubmitting;

  const form = useForm({
    initialValues: { email: '', display_name: '', password: '' },
    validate: {
      email:        (v) => (/^\S+@\S+$/.test(v) ? null : 'Invalid email'),
      display_name: (v) => (v.length >= 2 ? null : 'Display name too short'),
      password:     (v) => validatePasswordPolicy(v),
    },
  });
  const passwordRequirements = getPasswordRequirements(form.values.password, {
    email:       form.values.email,
    displayName: form.values.display_name,
  });

  const handleSubmit = form.onSubmit(async (values) => {
    const passwordError = validatePasswordPolicy(values.password, {
      email:       values.email,
      displayName: values.display_name,
    });
    if (passwordError) {
      form.setFieldError('password', passwordError);
      return;
    }

    try {
      setIsEmailSubmitting(true);
      await register(values);
    } catch (err: unknown) {
      const message = isAxiosError(err) ? (err.response?.data?.detail ?? 'Registration failed') : 'Registration failed';
      notifications.show({ color: 'red', title: 'Error', message });
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

      <Paper withBorder p="xl" mt="lg" radius="xs" className={classes.card}>
        <GoogleSignInButton
          fullWidth
          label={isGoogleSubmitting ? 'Creating Google session...' : 'Sign up with Google'}
          loading={isGoogleSubmitting}
          disabled={isProcessing}
          onSuccess={async (accessToken) => {
            try {
              setIsGoogleSubmitting(true);
              await loginWithGoogle(accessToken);
            } catch {
              notifications.show({ color: 'red', title: 'Google sign-in failed', message: 'Try again or register with email' });
            } finally {
              setIsGoogleSubmitting(false);
            }
          }}
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
            disabled={isProcessing}
            {...form.getInputProps('display_name')}
          />
          <TextInput
            className={classes.input}
            label="Email"
            placeholder="you@example.com"
            required
            mt="md"
            disabled={isProcessing}
            {...form.getInputProps('email')}
          />
          <PasswordInput
            className={classes.input}
            label="Password"
            placeholder="Create a strong password"
            required
            mt="md"
            disabled={isProcessing}
            {...form.getInputProps('password')}
          />
          <div className={classes.passwordRequirements} aria-label="Password requirements">
            <Text size="xs" fw={700} c="gray.3">
              Password requirements
            </Text>
            <ul className={classes.passwordRequirementList} aria-live="polite">
              {passwordRequirements.map((requirement) => (
                <li key={requirement.id} className={classes.passwordRequirement} data-met={requirement.met}>
                  <span className={classes.passwordRequirementIcon} aria-hidden="true">
                    {requirement.met ? <IconCheck size={12} stroke={2.2} /> : null}
                  </span>
                  <span>{requirement.label}</span>
                </li>
              ))}
            </ul>
          </div>

          {isProcessing && (
            <div className={classes.processingPanel} role="status" aria-live="polite" aria-atomic="true">
              <ThemeIcon radius="sm" color="ember" variant="light" size={34}>
                <IconUserPlus size={18} />
              </ThemeIcon>
              <div className={classes.processingContent}>
                <Text size="sm" fw={600}>
                  {isGoogleSubmitting ? 'Creating your Google session' : 'Creating your account'}
                </Text>
                <Text size="xs" c="dimmed">
                  We are setting up your profile and opening your GameRec library.
                </Text>
                <Progress value={68} color="ember" radius="xs" size="xs" mt={8} aria-label="Registration processing" />
              </div>
            </div>
          )}

          <Button type="submit" fullWidth mt="xl" loading={isEmailSubmitting} disabled={isProcessing}>
            {isEmailSubmitting ? 'Creating account...' : 'Register'}
          </Button>
        </form>
      </Paper>
    </Container>
    </div>
  );
}
