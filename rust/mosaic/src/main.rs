extern crate image;

use std::fs::File;
use std::path::Path;
use image::imageops::{resize, FilterType};
use image::GenericImage;

fn main() {
    // Use the open function to load an image from a Path.
    // ```open``` returns a dynamic image.
    let img = image::open(&Path::new("test.jpg")).unwrap();

    // The dimensions method returns the images width and height
    println!("dimensions {:?}", img.dimensions());

    // The color method returns the image's ColorType
    println!("{:?}", img.color());

    //this was Adam's idea -- i bet there's a faster way to do this
    let imgpixel = resize(&img, 1, 1, FilterType::Nearest);
    println!("reduced to color: {:?}", imgpixel.get_pixel(0,0));
    
    //sky: resize tiles and then with the new image do mosaic.copy_from(&tile, x, y)
    
    
    let ref mut fout = File::create(&Path::new("test.png")).unwrap();

    // Write the contents of this image to the Writer in PNG format.
    let _ = img.save(fout, image::PNG).unwrap();
}
