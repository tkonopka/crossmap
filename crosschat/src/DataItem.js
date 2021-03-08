import React from 'react';
import Box from '@material-ui/core/Box';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';
import docco from 'react-syntax-highlighter/dist/esm/styles/hljs/docco';
SyntaxHighlighter.registerLanguage('yaml', yaml);

const api_url = "http://"+process.env.REACT_APP_API_URL;


/** A display of raw content associated with a dataset item **/
class DataItem extends React.Component {
    constructor(props) {
        super(props);
        this.state = {"doc": null }
    }

    componentDidMount() {
        let params = this.props.match.params;
        let xhr = new XMLHttpRequest();
        let data_item = this;
        xhr.onload = function() {
            let result = JSON.parse(xhr.response);
            data_item.setState({"doc": result})
        };
        xhr.open("POST", api_url+"/document/", true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        let query = {"dataset": params.dataset, "id": params.id};
        xhr.send(JSON.stringify(query));
    }

    render() {
        let params = this.props.match.params;
        let doc = this.state.doc;
        if (doc === null) {
            return (<Box>Fetching data: {params.id} ({params.dataset})</Box>)
        }
        return(
            <Box className="data-item">
                <Box>Dataset: {decodeURIComponent(params.dataset)}</Box>
                <Box>ID: {decodeURIComponent(params.id)}</Box>
                <SyntaxHighlighter language="yaml" style={docco}>{doc}</SyntaxHighlighter>
            </Box>
        );
    }
}


export default DataItem;

