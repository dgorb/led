import React from 'react';
import { SketchPicker } from 'react-color';

class Main extends React.Component {
  state = {
    color: '#fff',
  };

  handleChange = (color, event) => {
    this.setState({ color: color.hex });
    setColor(color.rgb.r, color.rgb.g, color.rgb.b)
  };

  render() {
    return (
      <div>
          <SketchPicker
              color={ this.state.color }
              onChange={ this.handleChange }
          />
      </div>
    );
  }
}

function APICall(endpoint) {
  const url = 'http://192.168.1.10:5000';

  fetch(url + endpoint, {method: 'POST'})
    .then(response => {
      console.log(response)
    })
}

function setColor(r, g, b) {
  APICall(`/set-color?color=${r},${g},${b}`)

}

export default Main;
