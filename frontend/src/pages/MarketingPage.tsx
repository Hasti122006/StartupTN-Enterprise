import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  Grid,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  Schedule as ScheduleIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  History as HistoryIcon,
  Assessment as StatsIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

interface EmailCampaign {
  id: number;
  name: string;
  subject: string;
  body: string;
  target_sector: string | null;
  target_stage: string | null;
  target_location: string | null;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed';
  scheduled_time: string | null;
  sent_count: number;
  failed_count: number;
  created_at: string;
  updated_at: string;
}

interface CampaignDelivery {
  id: number;
  campaign: number;
  campaign_name: string;
  company: number;
  company_name: string;
  email_address: string;
  status: 'pending' | 'sent' | 'failed';
  sent_at: string | null;
  error_message: string | null;
}

interface MarketingStats {
  total_campaigns: number;
  scheduled_campaigns: number;
  sent_emails: number;
  failed_emails: number;
  success_rate: number;
}

export const MarketingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  
  // Dialog controls
  const [campaignDialogOpen, setCampaignDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<EmailCampaign | null>(null);
  
  // Campaign Form State
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [targetSector, setTargetSector] = useState('');
  const [targetStage, setTargetStage] = useState('');
  const [targetLocation, setTargetLocation] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');

  // Queries
  const { data: campaignsData, isLoading: isCampaignsLoading, refetch: refetchCampaigns } = useQuery<any>({
    queryKey: ['campaigns'],
    queryFn: async () => (await apiClient.get('/marketing/campaigns/')).data,
    refetchInterval: 5000,
  });
  const campaigns: EmailCampaign[] = campaignsData?.results || (Array.isArray(campaignsData) ? campaignsData : []);

  const { data: deliveriesData, isLoading: isDeliveriesLoading, refetch: refetchDeliveries } = useQuery<any>({
    queryKey: ['deliveries'],
    queryFn: async () => (await apiClient.get('/marketing/deliveries/')).data,
    refetchInterval: 5000,
  });
  const deliveries: CampaignDelivery[] = deliveriesData?.results || (Array.isArray(deliveriesData) ? deliveriesData : []);

  const { data: stats, refetch: refetchStats } = useQuery<MarketingStats>({
    queryKey: ['marketing-stats'],
    queryFn: async () => (await apiClient.get('/marketing/stats/')).data,
    refetchInterval: 5000,
  });

  const { data: sectorOptions = [] } = useQuery<string[]>({
    queryKey: ['filter-sectors'],
    queryFn: async () => (await apiClient.get('/companies/filters/sectors')).data,
  });

  const { data: stageOptions = [] } = useQuery<string[]>({
    queryKey: ['filter-stages'],
    queryFn: async () => (await apiClient.get('/companies/filters/stages')).data,
  });

  const handleOpenCreateDialog = () => {
    setSelectedCampaign(null);
    setName('');
    setSubject('');
    setBody('');
    setTargetSector('');
    setTargetStage('');
    setTargetLocation('');
    setCampaignDialogOpen(true);
  };

  const handleOpenEditDialog = (campaign: EmailCampaign) => {
    setSelectedCampaign(campaign);
    setName(campaign.name);
    setSubject(campaign.subject);
    setBody(campaign.body);
    setTargetSector(campaign.target_sector || '');
    setTargetStage(campaign.target_stage || '');
    setTargetLocation(campaign.target_location || '');
    setCampaignDialogOpen(true);
  };

  const handleSaveCampaign = async () => {
    const payload = {
      name,
      subject,
      body,
      target_sector: targetSector || null,
      target_stage: targetStage || null,
      target_location: targetLocation || null,
      status: 'draft',
    };

    try {
      if (selectedCampaign) {
        await apiClient.put(`/marketing/campaigns/${selectedCampaign.id}/`, payload);
      } else {
        await apiClient.post('/marketing/campaigns/', payload);
      }
      setCampaignDialogOpen(false);
      refetchCampaigns();
      refetchStats();
    } catch (error) {
      console.error('Failed to save campaign', error);
      alert('Error saving campaign. Please verify input fields.');
    }
  };

  const handleDeleteCampaign = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this email campaign?')) return;
    try {
      await apiClient.delete(`/marketing/campaigns/${id}/`);
      refetchCampaigns();
      refetchStats();
      refetchDeliveries();
    } catch (error) {
      console.error('Failed to delete campaign', error);
    }
  };

  const handleSendImmediately = async (id: number) => {
    if (!window.confirm('Send this campaign immediately to all matching companies?')) return;
    try {
      await apiClient.post(`/marketing/campaigns/${id}/send/`);
      refetchCampaigns();
      refetchStats();
    } catch (error) {
      console.error('Failed to trigger campaign sending', error);
    }
  };

  const handleOpenScheduleDialog = (campaign: EmailCampaign) => {
    setSelectedCampaign(campaign);
    setScheduleTime(campaign.scheduled_time ? campaign.scheduled_time.substring(0, 16) : '');
    setScheduleDialogOpen(true);
  };

  const handleScheduleCampaign = async () => {
    if (!selectedCampaign || !scheduleTime) return;
    try {
      await apiClient.post(`/marketing/campaigns/${selectedCampaign.id}/schedule/`, {
        scheduled_time: new Date(scheduleTime).toISOString(),
      });
      setScheduleDialogOpen(false);
      refetchCampaigns();
      refetchStats();
    } catch (error) {
      console.error('Failed to schedule campaign', error);
      alert('Failed to schedule campaign. Please check the datetime format.');
    }
  };

  const getStatusChip = (status: EmailCampaign['status']) => {
    const config = {
      draft: { label: 'Draft', color: 'default' as const },
      scheduled: { label: 'Scheduled', color: 'info' as const },
      sending: { label: 'Sending', color: 'warning' as const },
      sent: { label: 'Sent', color: 'success' as const },
      failed: { label: 'Failed', color: 'error' as const },
    };
    const current = config[status] || { label: status, color: 'default' as const };
    return <Chip label={current.label} color={current.color} size="small" sx={{ fontWeight: 600 }} />;
  };

  const formatTargetCriteria = (campaign: EmailCampaign) => {
    const criteria: string[] = [];
    if (campaign.target_sector) criteria.push(`Sector: ${campaign.target_sector}`);
    if (campaign.target_stage) criteria.push(`Stage: ${campaign.target_stage}`);
    if (campaign.target_location) criteria.push(`Loc: ${campaign.target_location}`);
    return criteria.length > 0 ? criteria.join(', ') : 'All Companies';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Email Marketing & Automation
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreateDialog}
          sx={{ borderRadius: 2 }}
        >
          Create Campaign
        </Button>
      </Box>

      {/* Metrics Section */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'primary.light', color: 'primary.contrastText', display: 'flex' }}>
                <EmailIcon fontSize="medium" />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Total Campaigns</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.total_campaigns}</Typography>
              </Box>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'info.light', color: 'info.contrastText', display: 'flex' }}>
                <ScheduleIcon fontSize="medium" />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Scheduled</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.scheduled_campaigns}</Typography>
              </Box>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'success.light', color: 'success.contrastText', display: 'flex' }}>
                <SendIcon fontSize="medium" />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Emails Sent</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.sent_emails}</Typography>
              </Box>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: stats.success_rate >= 90 ? 'success.light' : 'warning.light', color: 'primary.contrastText', display: 'flex' }}>
                <StatsIcon fontSize="medium" />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.success_rate}%</Typography>
              </Box>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)}>
          <Tab label="Automated Campaigns" icon={<EmailIcon />} iconPosition="start" sx={{ fontWeight: 600 }} />
          <Tab label="Delivery History & Logs" icon={<HistoryIcon />} iconPosition="start" sx={{ fontWeight: 600 }} />
        </Tabs>
      </Box>

      {/* TAB 1: Campaigns */}
      {activeTab === 0 && (
        <Box>
          {isCampaignsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
          ) : campaigns.length === 0 ? (
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              No email campaigns found. Click "Create Campaign" to get started!
            </Alert>
          ) : (
            <TableContainer component={Paper} sx={{ borderRadius: 2, overflow: 'hidden' }}>
              <Table>
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Campaign Name</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Subject</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Targets</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Scheduled Time</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Delivered</TableCell>
                    <TableCell sx={{ fontWeight: 600 }} align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {campaigns.map((campaign) => (
                    <TableRow key={campaign.id} hover>
                      <TableCell sx={{ fontWeight: 500 }}>{campaign.name}</TableCell>
                      <TableCell>{campaign.subject}</TableCell>
                      <TableCell>
                        <Tooltip title={formatTargetCriteria(campaign)}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {formatTargetCriteria(campaign)}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>{getStatusChip(campaign.status)}</TableCell>
                      <TableCell>
                        {campaign.scheduled_time
                          ? new Date(campaign.scheduled_time).toLocaleString()
                          : 'Not Scheduled'}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                          <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600 }}>
                            Sent: {campaign.sent_count}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 600 }}>
                            Failed: {campaign.failed_count}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                          {campaign.status !== 'sending' && (
                            <Tooltip title="Send Now">
                              <IconButton
                                color="primary"
                                size="small"
                                onClick={() => handleSendImmediately(campaign.id)}
                              >
                                <SendIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          {campaign.status !== 'sending' && (
                            <Tooltip title="Schedule">
                              <IconButton
                                color="info"
                                size="small"
                                onClick={() => handleOpenScheduleDialog(campaign)}
                              >
                                <ScheduleIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          {campaign.status !== 'sending' && (
                            <Tooltip title="Edit">
                              <IconButton
                                color="default"
                                size="small"
                                onClick={() => handleOpenEditDialog(campaign)}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete">
                            <IconButton
                              color="error"
                              size="small"
                              onClick={() => handleDeleteCampaign(campaign.id)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      {/* TAB 2: Delivery History & Logs */}
      {activeTab === 1 && (
        <Box>
          {isDeliveriesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
          ) : deliveries.length === 0 ? (
            <Alert severity="info" sx={{ borderRadius: 2 }}>No delivery logs available yet.</Alert>
          ) : (
            <TableContainer component={Paper} sx={{ borderRadius: 2, overflow: 'hidden' }}>
              <Table>
                <TableHead sx={{ bgcolor: 'action.hover' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Date & Time</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Campaign</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Target Company</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Email Address</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Errors / Details</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {deliveries.map((delivery) => (
                    <TableRow key={delivery.id} hover>
                      <TableCell>
                        {delivery.sent_at ? new Date(delivery.sent_at).toLocaleString() : 'Pending'}
                      </TableCell>
                      <TableCell sx={{ fontWeight: 500 }}>{delivery.campaign_name}</TableCell>
                      <TableCell>{delivery.company_name}</TableCell>
                      <TableCell>{delivery.email_address}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {delivery.status === 'sent' && <SuccessIcon color="success" fontSize="small" />}
                          {delivery.status === 'failed' && <ErrorIcon color="error" fontSize="small" />}
                          {delivery.status === 'pending' && <CircularProgress size={14} />}
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                            {delivery.status}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ color: 'error.main', fontSize: '0.85rem' }}>
                        {delivery.error_message || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      {/* Create / Edit Campaign Dialog */}
      <Dialog open={campaignDialogOpen} onClose={() => setCampaignDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {selectedCampaign ? 'Edit Email Campaign' : 'Create New Email Campaign'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
            <TextField
              label="Campaign Name"
              placeholder="e.g. Welcome new member startups"
              fullWidth
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <TextField
              label="Subject Line"
              placeholder="e.g. Welcome to StartupTN Enterprise Scraper Directory!"
              fullWidth
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            <TextField
              label="Campaign Email Body (HTML & Plaintext supported)"
              placeholder="Hi {founders},&#10;&#10;We wanted to connect with {company_name} to discuss new opportunities...&#10;&#10;Best,&#10;StartupTN Enterprise Team"
              multiline
              rows={8}
              fullWidth
              value={body}
              onChange={(e) => setBody(e.target.value)}
              helperText="Tip: Use {company_name} and {founders} template tags to personalize messages per recipient company."
            />

            <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 1 }}>
              Target Selection Filters (Optional)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <TextField
                  select
                  label="Filter by Sector"
                  fullWidth
                  value={targetSector}
                  onChange={(e) => setTargetSector(e.target.value)}
                >
                  <MenuItem value="">All Sectors</MenuItem>
                  {sectorOptions.map((sector) => (
                    <MenuItem key={sector} value={sector}>{sector}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  select
                  label="Filter by Stage"
                  fullWidth
                  value={targetStage}
                  onChange={(e) => setTargetStage(e.target.value)}
                >
                  <MenuItem value="">All Stages</MenuItem>
                  {stageOptions.map((stage) => (
                    <MenuItem key={stage} value={stage}>{stage}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Filter by Location"
                  placeholder="e.g. Chennai"
                  fullWidth
                  value={targetLocation}
                  onChange={(e) => setTargetLocation(e.target.value)}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setCampaignDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleSaveCampaign} variant="contained" disabled={!name || !subject || !body}>
            Save Campaign
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Campaign Dialog */}
      <Dialog open={scheduleDialogOpen} onClose={() => setScheduleDialogOpen(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Schedule Campaign</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1, minWidth: 320 }}>
            <Typography variant="body2" color="text.secondary">
              Set a date and time to automatically trigger sending the campaign.
            </Typography>
            <TextField
              type="datetime-local"
              fullWidth
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              label="Scheduled Execution Time"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setScheduleDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleScheduleCampaign} variant="contained" color="primary" disabled={!scheduleTime}>
            Schedule
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
