import { createTheme, PaletteMode } from '@mui/material';
import { blue, deepPurple, teal, grey } from '@mui/material/colors';

export const getTheme = (mode: PaletteMode) => createTheme({
    palette: {
        mode,
        ...(mode === 'light'
            ? {
                // Light Mode
                primary: {
                    main: deepPurple[600],
                },
                secondary: {
                    main: teal[400],
                },
                background: {
                    default: '#f3f4f6',
                    paper: '#ffffff',
                },
            }
            : {
                // Dark Mode
                primary: {
                    main: deepPurple[300],
                },
                secondary: {
                    main: teal[200],
                },
                background: {
                    default: '#0f172a',
                    paper: '#1e293b',
                },
            }),
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: {
            fontWeight: 700,
            fontSize: '2.5rem',
        },
        h4: {
            fontWeight: 600,
        },
        button: {
            textTransform: 'none',
            fontWeight: 600,
        },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    padding: '8px 24px',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none', // Remove default gradient in dark mode for cleaner look
                },
            },
        },
    },
});
