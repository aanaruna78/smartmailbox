import { createTheme, PaletteMode } from '@mui/material';

// Modern color palette
const primaryColor = {
  light: '#6366f1', // Indigo
  dark: '#818cf8',
};

const secondaryColor = {
  light: '#14b8a6', // Teal
  dark: '#2dd4bf',
};

export const getTheme = (mode: PaletteMode) =>
  createTheme({
    palette: {
      mode,
      ...(mode === 'light'
        ? {
            primary: { main: primaryColor.light },
            secondary: { main: secondaryColor.light },
            background: {
              default: '#f8fafc',
              paper: '#ffffff',
            },
            text: {
              primary: '#1e293b',
              secondary: '#64748b',
            },
          }
        : {
            primary: { main: primaryColor.dark },
            secondary: { main: secondaryColor.dark },
            background: {
              default: '#0f172a',
              paper: '#1e293b',
            },
            text: {
              primary: '#f1f5f9',
              secondary: '#94a3b8',
            },
          }),
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontWeight: 700, fontSize: '2.25rem', letterSpacing: '-0.025em' },
      h2: { fontWeight: 700, fontSize: '1.875rem', letterSpacing: '-0.025em' },
      h3: { fontWeight: 600, fontSize: '1.5rem' },
      h4: { fontWeight: 600, fontSize: '1.25rem' },
      h5: { fontWeight: 600, fontSize: '1.125rem' },
      h6: { fontWeight: 600, fontSize: '1rem' },
      body1: { fontSize: '0.9375rem', lineHeight: 1.6 },
      body2: { fontSize: '0.875rem', lineHeight: 1.5 },
      button: { textTransform: 'none', fontWeight: 600, fontSize: '0.9375rem' },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            padding: '10px 24px',
            boxShadow: 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)',
            },
          },
          contained: {
            background: `linear-gradient(135deg, ${primaryColor.light} 0%, #8b5cf6 100%)`,
            '&:hover': {
              background: `linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)`,
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)',
            transition: 'box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out',
          },
          elevation1: {
            boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)',
          },
          elevation3: {
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
            borderRadius: 8,
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            padding: '14px 16px',
          },
          head: {
            fontWeight: 600,
            backgroundColor: 'transparent',
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            transition: 'background-color 0.15s ease',
          },
        },
      },
    },
  });
