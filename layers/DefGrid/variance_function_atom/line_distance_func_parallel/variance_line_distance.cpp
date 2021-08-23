#include <THC/THC.h>
#include <torch/torch.h>

#include <vector>
#include<stdio.h>
extern THCState *state;
// C++ interface

#define CHECK_CUDA(x) AT_ASSERTM(x.type().is_cuda(), #x " must be a CUDA tensor")
#define CHECK_CONTIGUOUS(x) AT_ASSERTM(x.is_contiguous(), #x " must be contiguous")
#define CHECK_INPUT(x) CHECK_CUDA(x); CHECK_CONTIGUOUS(x)

#define CHECK_DIM3(x, b, h, w, d) AT_ASSERTM((x.size(0) == b) && (x.size(1) == h) && (x.size(2) == w) && (x.size(3) == d), #x " must be same im size")
#define CHECK_DIM2(x, b, f, d) AT_ASSERTM((x.size(0) == b) && (x.size(1) == f) && (x.size(2) == d), #x " must be same point size")
#define CHECK_DIM4(x, b, h, w, d, k) AT_ASSERTM((x.size(0) == b) && (x.size(1) == h) && (x.size(2) == w) && (x.size(3) == d) && (x.size(4) == k), #x " must be same im size")

void line_variance_parallel_cuda_forward_batch(at::Tensor img_fea_bxnxd, at::Tensor grid_fea_bxkxd, at::Tensor grid_bxkx3x2, at::Tensor img_pos_bxnx2,
                        at::Tensor variance_bxn, float sigma, at::Tensor reconstruct_bxn, at::Tensor buffer_bxnxk, at::Tensor buffer_bxn, at::Tensor buffer_bxnx4, at::Tensor buffer_bxnxdx4, int split_size);

void line_variance_parallel_forward_batch(at::Tensor img_fea_bxnxd, at::Tensor grid_fea_bxkxd, at::Tensor grid_bxkx3x2, at::Tensor img_pos_bxnx2,
                        at::Tensor variance_bxn, float sigma, at::Tensor reconstruct_bxn, at::Tensor buffer_bxnxk, at::Tensor buffer_bxn, at::Tensor buffer_bxnx4, at::Tensor buffer_bxnxdx4, int split_size) {
	CHECK_INPUT(grid_bxkx3x2);
	CHECK_INPUT(img_pos_bxnx2);
	CHECK_INPUT(variance_bxn);
	CHECK_INPUT(img_fea_bxnxd);
	CHECK_INPUT(grid_fea_bxkxd);
	CHECK_INPUT(reconstruct_bxn);
	CHECK_INPUT(buffer_bxnxk);
	CHECK_INPUT(buffer_bxn);
	CHECK_INPUT(buffer_bxnx4);
	CHECK_INPUT(buffer_bxnxdx4);


	int bnum = grid_bxkx3x2.size(0);
	int n_grid = grid_bxkx3x2.size(1);
	int n_pixel = img_pos_bxnx2.size(1);
	int d_fea = img_fea_bxnxd.size(2);

	CHECK_DIM3(grid_bxkx3x2, bnum, n_grid, 3, 2);
	CHECK_DIM2(img_pos_bxnx2, bnum, n_pixel, 2);
	CHECK_DIM2(img_fea_bxnxd, bnum, n_pixel, d_fea);
	CHECK_DIM2(grid_fea_bxkxd, bnum, n_grid, d_fea);
    CHECK_DIM2(reconstruct_bxn, bnum, n_pixel, d_fea);
	line_variance_parallel_cuda_forward_batch(img_fea_bxnxd, grid_fea_bxkxd, grid_bxkx3x2, img_pos_bxnx2, variance_bxn, sigma, reconstruct_bxn, buffer_bxnxk, buffer_bxn, buffer_bxnx4, buffer_bxnxdx4, split_size);

	return;
}

void line_variance_parallel_cuda_backward_batch(at::Tensor dldvariance_bxn, at::Tensor img_fea_bxnxd, at::Tensor grid_fea_bxkxd, at::Tensor grid_bxkx3x2, at::Tensor img_pos_bxnx2,
                         float sigma, at::Tensor dldreconstruct_bxnxd, at::Tensor buffer_bxnxk, at::Tensor dldgrid_bxkx3x2, at::Tensor buffer_bxn, at::Tensor buffer_bxnx4, int split_size);

void line_variance_parallel_backward_batch(at::Tensor dldvariance_bxn, at::Tensor img_fea_bxnxd, at::Tensor grid_fea_bxkxd, at::Tensor grid_bxkx3x2, at::Tensor img_pos_bxnx2,
                        float sigma, at::Tensor dldreconstruct_bxnxd, at::Tensor buffer_bxnxk, at::Tensor dldgrid_bxkx3x2, at::Tensor buffer_bxn, at::Tensor buffer_bxnx4, int split_size) {

	CHECK_INPUT(grid_bxkx3x2);
	CHECK_INPUT(img_pos_bxnx2);
	CHECK_INPUT(dldvariance_bxn);
	CHECK_INPUT(img_fea_bxnxd);
	CHECK_INPUT(grid_fea_bxkxd);
	CHECK_INPUT(dldreconstruct_bxnxd);
	CHECK_INPUT(buffer_bxnxk);
	CHECK_INPUT(buffer_bxn);
	CHECK_INPUT(buffer_bxnx4);

	int bnum = grid_bxkx3x2.size(0);
	int n_grid = grid_bxkx3x2.size(1);
	int n_pixel = img_pos_bxnx2.size(1);
	int d_fea = img_fea_bxnxd.size(2);

	CHECK_DIM3(grid_bxkx3x2, bnum, n_grid, 3, 2);
	CHECK_DIM2(img_pos_bxnx2, bnum, n_pixel, 2);
	CHECK_DIM2(img_fea_bxnxd, bnum, n_pixel, d_fea);
	CHECK_DIM2(grid_fea_bxkxd, bnum, n_grid, d_fea);
    CHECK_DIM3(dldgrid_bxkx3x2, bnum, n_grid, 3, 2);
    CHECK_DIM2(dldreconstruct_bxnxd, bnum, n_pixel, d_fea);
    CHECK_DIM2(buffer_bxnxk, bnum, n_pixel, n_grid);

	line_variance_parallel_cuda_backward_batch(dldvariance_bxn, img_fea_bxnxd, grid_fea_bxkxd, grid_bxkx3x2, img_pos_bxnx2, sigma,
	                        dldreconstruct_bxnxd, buffer_bxnxk, dldgrid_bxkx3x2, buffer_bxn, buffer_bxnx4, split_size);

	return;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
	m.def("forward", &line_variance_parallel_forward_batch, "dr forward batch (CUDA)");
	m.def("backward", &line_variance_parallel_backward_batch, "dr backward batch (CUDA)");
}
