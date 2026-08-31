use std::path::Path;
use ort::session::Session;
use ort::value::Value;
use ndarray::Array2;

pub struct GraphSession {
    session: Session,
}

impl GraphSession {
    ///  extracted ONNX graph into a new ORT session
    pub fn new(model_path: impl AsRef<Path>) -> Result<Self, ort::Error> {
        let session = Session::builder()?
            .commit_from_file(model_path)?;
        Ok(Self { session })
    }

    /// Run one forward pass through the loaded ONNX graph with a synthetic or real input tensor
    /// Expected input length: 128 (corresponding to shape [1, 128]).
    /// Returns the output vector of floats.
    pub fn run(&mut self, input: &[f32]) -> Result<Vec<f32>, ort::Error> {
        if input.len() != 128 {
            return Err(ort::Error::new(format!(
                "Invalid input length: expected 128, got {}",
                input.len()
            )));
        }

        // Reshape flat input slice into a 2D Array [1, 128]
        let array = Array2::from_shape_vec((1, 128), input.to_vec())
            .map_err(|e| ort::Error::new(e.to_string()))?;

        // Convert the array into an ORT Value (Tensor)
        let input_value = Value::from_array(array)?;

        // Run the forward pass with named input
        let outputs = self.session.run(ort::inputs!["input" => input_value])?;

        // Extract the output tensor by its ONNX graph output name
        let output_value = outputs
            .get("output")
            .ok_or_else(|| ort::Error::new("Output 'output' not found in graph outputs"))?;

        // In ort 2.x, try_extract_tensor returns a tuple of (&Shape, &[T])
        let (_shape, data) = output_value.try_extract_tensor::<f32>()?;
        Ok(data.to_vec())
    }
}

// Enforce lane isolation guidelines by asserting Send + Sync compatibility
const _: () = {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<GraphSession>;
};
