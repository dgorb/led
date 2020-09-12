import React, {useState, useEffect} from 'react';
import {ChromePicker, CirclePicker} from 'react-color';
import Heart from "react-animated-heart";

function Main() {
  const [color, setColor] = useState({});
  const [hex, setHex] = useState("");

  useEffect(() => {
    initColorAPI().then(response => {
      response.json().then(data => {
        setColor(data);
      })
    })
  }, []);

  let handleChange = (color, event) => {
    setColor(color.rgb);
    setHex(color.hex);
    setColorAPI(color.rgb.r, color.rgb.g, color.rgb.b)
  };

  return (
    <div style={{
      height: '100vh',
      width: '100wv',
      background: `rgb(${color.r}, ${color.g}, ${color.b})`
      }}>
        <ChromePicker
          color={color}
          onChange={handleChange}
          disableAlpha={true}
        />
        <Like color={hex} setColor={setColor} />
    </div>
  );
}

function Like(props) {
  const [isClick, setClick] = useState(false);
  const [favorites, setFavorites] = useState();

  useEffect(() => {
    favoritesAPI().then(response => {
      response.json().then(data => {
        setFavorites(data);
      })
    })
  }, []);

  useEffect(() => {
    if (isClick) {
      setClick(false);
    }
  }, [props.color]);

  useEffect(() => {
    favoritesAPI().then(response => {
      response.json().then(data => {
        setFavorites(data);
      })
    })
  }, [isClick]);

  let handleChange = (color, event) => {
    props.setColor(color.rgb);
    setColorAPI(color.rgb.r, color.rgb.g, color.rgb.b)
  };

  return (
    <>
    <div>
      <Heart isClick={isClick} onClick={() => {
          likeAPI(props.color.replace('#', ''));
          setClick(!isClick)
      }} />
    </div>
    <div style={{backgroundColor: 'white', width: '252px'}}>
      <p>Favorites</p>
      <CirclePicker
        onChange={handleChange}
        colors={favorites}
      />
    </div>
    </>
  );
}

function APICall(method, endpoint) {
  const url = 'http://192.168.1.10:5000';
  return fetch(url + endpoint, {method: method})
}

function setColorAPI(r, g, b) {
  APICall("POST", `/set-color?color=${r},${g},${b}`)
}

function initColorAPI() {
  return APICall("GET", '/get-color');
}

function likeAPI(hex) {
  APICall("POST", `/favorite?color=${hex}`)
}

function favoritesAPI() {
  return APICall("GET", '/favorites')
}

export default Main;
