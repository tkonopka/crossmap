import React from 'react';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';


/**
 * A Form to compose the content of a query
 *
 * The form can display in a basic and extended format.
 * The basic format has only one text area.
 * The extended format has an additional text area for negative-weight
 * keywords
 *
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
                    <TextField id="query-data-pos" autoFocus fullWidth multiline rowsMax={8}
                               onKeyPress={(e) => this.handleKeyPress(e) }
                               value={this.props.data_pos}
                               onInput={(e) => this.props.update("data_pos", e.target.value)}
                               label="Query" margin="normal"/>
                    <TextField id="query-data-neg" fullWidth multiline rowsMax={8}
                               value={this.props.data_neg}
                               onKeyPress={(e) => this.handleKeyPress(e) }
                               onInput={(e) => this.props.update("data_neg", e.target.value)}
                               label="Query (negative weight)" margin="normal"/>
                </Grid>
            </Grid>
            </form>
        )
    }
}

export default ControllerQueryForm;
