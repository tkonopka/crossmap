import React from 'react';
import ReactDOM from 'react-dom';
import Crosschat from './Crosschat';

it('renders without crashing', () => {
  const div = document.createElement('div');
  ReactDOM.render(<Crosschat />, div);
  ReactDOM.unmountComponentAtNode(div);
});
