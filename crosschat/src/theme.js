// styling for Material-ui components
import { createMuiTheme } from '@material-ui/core/styles';

const theme = createMuiTheme({
    props: {
        MuiButtonBase: {
            disableRipple: true, // disable ripple on all the buttons
        }
    }
});

export default theme;