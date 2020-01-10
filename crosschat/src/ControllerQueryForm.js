import React from 'react';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import Box from '@material-ui/core/Box';


/**
 * A Form to compose the content of a query (primary data and auxiliary fields).
 */
class ControllerQueryForm extends React.Component {
    constructor(props) {
        super(props);
        this.handleKeyPress = this.handleKeyPress.bind(this);
    }

    /** this handler can submit the query with Ctrl+Enter **/
    handleKeyPress(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            this.props.send()
        }
    }

    render() {
        return(<form autoComplete="off">
            <Grid container spacing={1}>
                <Grid item xs={12}>
                    <TextField id="query-data" autoFocus fullWidth multiline rowsMax={8}
                               onKeyPress={(e) => this.handleKeyPress(e) }
                               value={this.props.data}
                               onInput={(e) => this.props.update("data", e.target.value)}
                               label="Query" margin="normal"/>
                    <Box display={this.props.extended ? "block": "none"}>
                        <TextField id="query-aux-pos" fullWidth multiline rowsMax={8}
                                   value={this.props.aux_pos}
                                   onKeyPress={(e) => this.handleKeyPress(e) }
                                   onInput={(e) => this.props.update("aux_pos", e.target.value)}
                                   label="Auxiliary data (positive weight)" margin="normal"/>
                        <TextField id="query-aux-neg" fullWidth multiline rowsMax={8}
                                   value={this.props.aux_neg}
                                   onKeyPress={(e) => this.handleKeyPress(e) }
                                   onInput={(e) => this.props.update("aux_neg", e.target.value)}
                                   label="Auxiliary data (negative weight)" margin="normal"/>
                    </Box>
                </Grid>
            </Grid>
            </form>
        )
    }
}

export default ControllerQueryForm;
