import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Card,
  CardContent,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Divider,
  Stack,
  Chip,
} from '@mui/material';
import { Security as SecurityIcon, OpenInNew as LaunchIcon, CheckCircle as CheckIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberSession, setRememberSession] = useState(true);
  const [checking, setChecking] = useState(false);

  const loginUrl = import.meta.env.VITE_STARTUPTN_LOGIN_URL || 'https://startuptn.in/login';

  const { data: authStatus, refetch } = useQuery({
    queryKey: ['auth-status'],
    queryFn: async () => (await apiClient.get('/scraper/auth-status')).data,
    refetchInterval: 3000,
  });

  const handleManualLoginOpen = () => {
    window.open(loginUrl, '_blank', 'noopener,noreferrer');
  };

  const handleVerifySession = async () => {
    setChecking(true);
    const result = await refetch();
    setChecking(false);
    if (result.data?.authenticated) {
      navigate('/scraper', { replace: true });
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justify: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 540, width: '100%', borderRadius: 3, boxShadow: 6 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header & Logo */}
          <Box sx={{ textCenter: 'center', textAlign: 'center', mb: 3 }}>
            <Box
              component="img"
              src="https://startuptn.in/images/logo.png"
              alt="StartupTN Logo"
              onError={(e: any) => { e.target.style.display = 'none'; }}
              sx={{ maxHeight: 50, mb: 1 }}
            />
            <Typography variant="h4" sx={{ fontWeight: 800, color: 'primary.main', mb: 0.5 }}>
              StartupTN Enterprise Scraper
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Secure Authenticated Scraper & Intelligence Portal
            </Typography>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {/* Session Status Banner */}
          {authStatus?.authenticated ? (
            <Alert
              icon={<CheckIcon fontSize="inherit" />}
              severity="success"
              action={
                <Button color="inherit" size="small" onClick={() => navigate('/scraper')}>
                  Go to Scraper
                </Button>
              }
              sx={{ mb: 3 }}
            >
              Authenticated StartupTN Session Detected!
            </Alert>
          ) : (
            <Alert severity="warning" icon={<SecurityIcon />} sx={{ mb: 3 }}>
              StartupTN login requires manual CAPTCHA verification.
            </Alert>
          )}

          {/* Credentials Inputs (stored only in component state, never printed or saved plaintext) */}
          <Stack spacing={2} sx={{ mb: 3 }}>
            <TextField
              label="StartupTN Username / Email"
              variant="outlined"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. user@example.com"
            />
            <TextField
              label="StartupTN Password"
              type="password"
              variant="outlined"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={rememberSession}
                  onChange={(e) => setRememberSession(e.target.checked)}
                  color="primary"
                />
              }
              label="Remember session state"
            />
          </Stack>

          {/* Manual Login Guidance Box */}
          <Box
            sx={{
              p: 2,
              bgcolor: 'action.hover',
              borderRadius: 2,
              mb: 3,
              border: '1px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              Manual CAPTCHA Flow Steps:
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph sx={{ mb: 1 }}>
              1. Click <strong>Open StartupTN Login Page</strong> to complete CAPTCHA in the official portal.
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph sx={{ mb: 1 }}>
              2. Alternatively run: <code>python scraper/save_auth_state.py --storage .runtime/startuptn-auth-state.json</code>
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0 }}>
              3. Click <strong>Verify Session</strong> below to launch the scraper control dashboard.
            </Typography>
          </Box>

          {/* Action Buttons */}
          <Stack spacing={2}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={<LaunchIcon />}
              onClick={handleManualLoginOpen}
              fullWidth
            >
              Open StartupTN Portal & CAPTCHA
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              size="large"
              onClick={handleVerifySession}
              disabled={checking}
              fullWidth
            >
              {checking ? 'Checking Session...' : 'Verify Session & Continue to Scraper'}
            </Button>
          </Stack>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Chip
              label={authStatus?.authenticated ? 'Session Active' : 'Session Pending Login'}
              color={authStatus?.authenticated ? 'success' : 'default'}
              size="small"
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
