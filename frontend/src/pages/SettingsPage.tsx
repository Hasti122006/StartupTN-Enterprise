import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';

export const SettingsPage: React.FC = () => {
  const [message, setMessage] = React.useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(true);
  };

  return (
    <Box component="form" onSubmit={handleSave}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        System Settings
      </Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(false)}>
          These settings are deployment-managed. Update the private environment configuration and restart the affected service; this screen does not persist secrets or runtime configuration.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Scraper Defaults */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Default Scraper Parameters
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="Target Base URL"
                    fullWidth
                    defaultValue="https://startuptn.in/ecosystem-info"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField label="Default Parallel Workers" type="number" fullWidth defaultValue={2} />
                </Grid>
                <Grid item xs={6}>
                  <TextField label="Default Timeout (sec)" type="number" fullWidth defaultValue={30} />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications & Integration Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                n8n & Notification Webhooks
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="Slack Webhook URL"
                    fullWidth
                    placeholder="https://hooks.slack.com/services/..."
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Notification Email"
                    fullWidth
                    placeholder="admin@company.com"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Enable Automated Email Alerts on Failure"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Button type="submit" variant="contained" color="primary" size="large" startIcon={<InfoIcon />}>
            Show Configuration Instructions
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};
