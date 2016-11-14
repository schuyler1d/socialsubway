extern crate image;

use std::{f32};
use std::fs::File;
use std::path::Path;
use std::fmt::Debug;
use std::convert::Into;

use image::imageops::{resize, FilterType};
use image::{GenericImage, DynamicImage};
use image::{Rgba, Pixel};
use image::Primitive;

#[derive(Debug)]
struct Hls(f32, f32, f32);

fn rgb2hls<T:Primitive+Debug+Into<f32>>(p: Rgba<T>) -> Hls
{
    let r:f32 = p.data[0].into() /255.0;
    let g:f32 = p.data[1].into() /255.0;
    let b:f32 = p.data[2].into() /255.0;
    //let (r,g,b) = (p.data[0].into(), p.data[1].into(), p.data[2].into());

    let minc = r.min(g.min(b));
    let maxc = r.max(g.max(b));

    let l = (minc+maxc) / 2.0;
    if minc == maxc {
        return Hls(0.0, l, 0.0)
    }

    let diffc = maxc-minc;
    let s = if l <= 0.5 {
        diffc / (maxc+minc)
        } else {
        diffc / (2.0-maxc-minc)
    };

    let mut h = if maxc == r { ((maxc-b) / diffc) - ((maxc-g) / diffc) 
    }  else if maxc == g { 2.0 + ((maxc-r) / diffc) - ((maxc-b) / diffc)
    }  else {              4.0 + ((maxc-g) / diffc) - ((maxc-r) / diffc) };
    h /= 6.0;
    if h.is_sign_negative() {
        h = 6.0 - h;
    }

    Hls(h.fract(), l, s)
    //  Hls(1.0,1.0,1.0)
}

//fn average_hls_color<T>(image: &T) -> Hls
//where T:GenericImage//<Pixel=Rgba<u8>> 
fn average_hls_color(image: &DynamicImage) -> Hls
{
    let (w,h) = image.dimensions();
    let num_pixels = w * h;

    let rgb_sum = image.pixels().fold( (0i32, 0i32, 0i32),
                          |acc, p| { let x = p.2.data; //the pixel color
                                     //(acc.0 + x.0, acc.1+x.1, acc.2+x.2)
                                     (acc.0 + x[0] as i32, acc.1+x[1] as i32, acc.2+x[2] as i32)
                          }
    );
    let rgba = Rgba([(rgb_sum.0 as f32/(num_pixels as f32)).round(),
                    (rgb_sum.1 as f32/(num_pixels as f32)).round(),
                    (rgb_sum.2 as f32/(num_pixels as f32)).round(),
                    0.0]);
    println!("rgb average {:?}", rgba);
    rgb2hls(rgba)
    //Hls(0.0,0.0,0.0)
}

fn main() {
    // Use the open function to load an image from a Path.
    // ```open``` returns a dynamic image.
    let img = image::open(&Path::new("test.jpg")).unwrap();

    // The dimensions method returns the images width and height
    println!("dimensions {:?}", img.dimensions());

    // The color method returns the image's ColorType
    println!("{:?}", img.color());

    println!("red: {:?}", rgb2hls(Rgba([256.0, 0.0, 0.0, 0.0])));
    println!("green: {:?}", rgb2hls(Rgba([0.0, 256.0, 0.0, 0.0])));
    println!("blue: {:?}", rgb2hls(Rgba([0.0, 0.0, 256.0, 0.0])));
    println!("black: {:?}", rgb2hls(Rgba([0.0, 0.0, 0.0, 0.0])));
    println!("white: {:?}", rgb2hls(Rgba([256.0, 256.0, 256.0, 0.0])));

    ///////////////////////////////////////
    // get average pixel color
    //let numpixels = img.width * img.height;
    let imgpixel = average_hls_color(&img);
    println!("reduced to color: {:?} huedegrees: {:?}", imgpixel, imgpixel.0 * 360.0);

    // This was Adam's idea -- i bet there's a faster way to do this
    // The reason why it's slower is that this averages horizontally
    //   and then in a second pass, averages vertically, but we
    let imgpixel_adam = resize(&img, 1, 1, FilterType::Nearest);
    let imgcolor_adam = imgpixel_adam.get_pixel(0,0).to_rgba();
    println!("reduced to rgb (Adam method): {:?}", imgcolor_adam);
    println!("reduced to hsl (Adam method): {:?}", rgb2hls(imgcolor_adam));
    
    //sky: resize tiles and then with the new image do mosaic.copy_from(&tile, x, y)
    
    ////////////////////////////////////////
    // image-type conversion and save example
    let ref mut fout = File::create(&Path::new("test.png")).unwrap();

    // Write the contents of this image to the Writer in PNG format.
    let _ = img.save(fout, image::PNG).unwrap();
}
