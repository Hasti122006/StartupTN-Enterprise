import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Badge,
  Menu,
  MenuItem,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Notifications as NotificationsIcon,
  CheckCircle as ConnectedIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useAppTheme } from '../../context/ThemeContext';
import { apiClient } from '../../api/client';

interface NavbarProps {
  onMenuClick: () => void;
}

const AuthStatusBadge: React.FC = () => {
  const { data } = useQuery({
    queryKey: ['auth-status'],
    queryFn: async () => (await apiClient.get('/scraper/auth-status')).data,
    refetchInterval: 5000,
  });

  const isAuth = Boolean(data?.authenticated);

  return (
    <Chip
      size="small"
      icon={isAuth ? <ConnectedIcon fontSize="small" /> : <WarningIcon fontSize="small" />}
      label={isAuth ? 'Session: Connected' : 'Session: Login Required'}
      color={isAuth ? 'success' : 'warning'}
      variant="outlined"
      sx={{ fontWeight: 600, mr: 1 }}
    />
  );
};

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { mode, toggleTheme } = useAppTheme();
  const [notifAnchorEl, setNotifAnchorEl] = useState<null | HTMLElement>(null);

  const handleNotifOpen = (e: React.MouseEvent<HTMLElement>) => setNotifAnchorEl(e.currentTarget);
  const handleNotifClose = () => setNotifAnchorEl(null);

  return (
    <AppBar
      position="sticky"
      color="default"
      elevation={0}
      sx={{
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton
            color="inherit"
            edge="start"
            onClick={onMenuClick}
            sx={{ display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, display: { xs: 'none', sm: 'block' } }}>
            StartupTN Data Intelligence Platform
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Session Status Chip */}
          <AuthStatusBadge />

          {/* Dark Mode Toggle */}
          <Tooltip title={`Switch to ${mode === 'dark' ? 'Light' : 'Dark'} Mode`}>
            <IconButton onClick={toggleTheme} color="inherit">
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Notifications Bell */}
          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={handleNotifOpen}>
              <Badge badgeContent={3} color="primary">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={notifAnchorEl}
            open={Boolean(notifAnchorEl)}
            onClose={handleNotifClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleNotifClose}>
              <Typography variant="body2">System health: All services operational</Typography>
            </MenuItem>
            <MenuItem onClick={handleNotifClose}>
              <Typography variant="body2">Daily schedule ready for execution</Typography>
            </MenuItem>
            <MenuItem onClick={handleNotifClose}>
              <Typography variant="body2">Database backup completed</Typography>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
