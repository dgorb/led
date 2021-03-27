import React, {useState, useEffect, useRef} from 'react';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import Slider from '@material-ui/core/Slider';
import {CirclePicker} from 'react-color';
import ColorDisplay from './ColorDisplay.jsx'
import {HSVtoRGB, RGBtoHEX, RGBtoHSV, coordsToHSV, HSVToCoords, distance, distanceWithoutR} from '../scripts/utils.js';

// TODO: calculate dynamically based on image/img element dimensions?
const D = 250; // Color wheel image width/height
const R = D / 2; // Color wheel "radius", half of image
                 // (assuming that the color wheel takes up the whole image)

export default function ColorPicker(props) {
    const [color, setColor] = useState(props.color);
    const [cursorCoords, setCursorCoords] = useState([0, 0]);
    const [pageX, setPageX] = useState(0);
    const [pageY, setPageY] = useState(0);
    const wheelRef = useRef(null);

    useEffect(() => {
       setCursor(color);
    }, [])

    useEffect(() => {
        if (color.hex !== props.color.hex) {
            setColor(props.color);
            setCursor(props.color);
        }
    }, [props.color])

    const setCursor = (color) => {
        const initCursorCoords = HSVToCoords(color.hsv, R);
        setPageX(initCursorCoords[0] + wheelRef.current.getBoundingClientRect().x);
        setPageY(initCursorCoords[1] + wheelRef.current.getBoundingClientRect().y);
    }

    const onMouseMove = (e) => {
        // Only pick color when pressing the left mouse button
        if (e.buttons == 1 || e.type == 'click') {
            let clr = colorFromCoords(
                Math.round(e.pageX - wheelRef.current.getBoundingClientRect().x),
                Math.round(e.pageY - wheelRef.current.getBoundingClientRect().y),
            );
            setColor(clr);
            setPageX(e.pageX);
            setPageY(e.pageY);
            props.onChange(clr, e);
            props.setColor(clr);
        }
    }

    // Mobile
    const onTouch = (e) => {
        let clr = colorFromCoords(
            Math.round(e.touches[0].pageX - wheelRef.current.getBoundingClientRect().x),
            Math.round(e.touches[0].pageY - wheelRef.current.getBoundingClientRect().y),
        );
        setColor(clr);
        setPageX(e.touches[0].pageX);
        setPageY(e.touches[0].pageY);
        props.onChange(clr,  e);
        props.setColor(clr);
    }

    const onBrightnessChange = (e, value) => {
        if (value != color.hsv[2]) {
            setColor({...color, hsv: [
                color.hsv[0],
                color.hsv[1],
                value,
            ]})

            let hsv = [color.hsv[0], color.hsv[1], value];
            let rgb = HSVtoRGB(color.hsv[0], color.hsv[1], value);
            let hex = RGBtoHEX(rgb);
            let clr = {
                hsv: hsv,
                rgb: rgb,
                hex: hex,
            }
            setColor(clr)
            props.onChange(clr, e);
        }
    }

    const colorFromCoords = (x, y) => {
        let d = distance(R, x, y);
        if (d <= R) { // Only calculate color if we're within the color wheel
            const hsv = coordsToHSV(x, y, R, color.hsv[2]);
            const rgb = HSVtoRGB(hsv[0], hsv[1], hsv[2]);
            const hex = RGBtoHEX(rgb);
            return {
                hsv: hsv,
                rgb: rgb,
                hex: hex,
            }
        } else {
            return color;
        }
    }

    const wheelCenter = () => {
        if (wheelRef.current) {
            let wheel = wheelRef.current.getBoundingClientRect();
            let centerX = wheel.x + wheel.width / 2;
            let centerY = wheel.y + wheel.height / 2;
            return [centerX, centerY];
        } else {
            return [0, 0];
        }
    }

    const insideWheel = (x, y) => {
        // TODO: Calculate radius dynamically
        let [centerX, centerY] = wheelCenter();
        let d = distanceWithoutR(x, y, centerX, centerY);
        if (d <= R) {
            return true
        }

        return false
    }

    return (
        <div style={{width: window.innerWidth, backgroundColor: "white", paddingLeft: "10px", paddingRight: "10px"}}>
            <img className="nodrag" width="250px" height="250px" src="/color-wheel.png"
                ref={wheelRef}
                onClick={onMouseMove}
                onMouseMove={onMouseMove}
                onTouchMove={onTouch}
                onTouchStart={onTouch}
            />
            <BrightnessSlider value={color.hsv[2]} onChange={onBrightnessChange} />
            <br />
            { props.showCurrentColor && <ColorDisplay color={color} /> }
            <Cursor x={pageX} y={pageY} insideWheel={insideWheel(pageX, pageY)} />
        </div>
    )
}

function BrightnessSlider(props) {
    const handleChange = (event, val) => {
        props.onChange(event, val);
    }

    return (
        <div style={{width: "90%", backgroundColor: "white", paddingRight: "3%"}}>
            <Typography id="continuous-slider" gutterBottom>
                Brightness
            </Typography>
            <Slider
                value={props.value}
                onChange={handleChange}
                min={0.0}
                max={1.0}
                step={0.01}
                aria-labelledby="continuous-slider"
            />
        </div>
    )
}

function Cursor(props) {
    const [x, setX] = useState(props.x);
    const [y, setY] = useState(props.y);

    useEffect(() => {
        if (props.insideWheel) {
            setX(props.x);
            setY(props.y);
        }
    }, [props.x, props.y]);

    return (
        <div className='nodrag' style={{position: "absolute", top: y, left: x, cursor: "default"}}>
            <div className='picker-cursor nodrag'></div>
        </div>
    )
}
