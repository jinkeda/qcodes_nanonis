import numpy as np
import pytest

from nanonis.workflows.scan import ScanFrame, scan_coordinate_grids


def test_unrotated_pixel_centres():
    frame = ScanFrame(center_x=0.0, center_y=0.0, width=4.0, height=4.0, angle=0.0)
    x, y = scan_coordinate_grids(frame, pixels=2, lines=2, row_order="bottom_to_top")
    # cols [0.5, 1.5] -> local_x [-1, 1]; bottom_to_top rows -> local_y [-1, 1].
    assert x.shape == (2, 2)
    np.testing.assert_allclose(x, [[-1.0, 1.0], [-1.0, 1.0]])
    np.testing.assert_allclose(y, [[-1.0, -1.0], [1.0, 1.0]])  # row 0 at bottom


def test_row_order_flips_y():
    frame = ScanFrame(center_x=0.0, center_y=0.0, width=4.0, height=4.0, angle=0.0)
    _, y_bt = scan_coordinate_grids(frame, 2, 2, row_order="bottom_to_top")
    _, y_tb = scan_coordinate_grids(frame, 2, 2, row_order="top_to_bottom")
    np.testing.assert_allclose(y_tb, y_bt[::-1])  # row order reverses the slow axis


def test_column_order_flips_x():
    frame = ScanFrame(center_x=0.0, center_y=0.0, width=4.0, height=4.0, angle=0.0)
    x_lr, _ = scan_coordinate_grids(frame, 2, 2, row_order="bottom_to_top")
    x_rl, _ = scan_coordinate_grids(
        frame, 2, 2, row_order="bottom_to_top", column_order="right_to_left"
    )
    np.testing.assert_allclose(x_rl, x_lr[:, ::-1])


def test_center_offset_translates():
    frame = ScanFrame(center_x=10.0, center_y=-5.0, width=4.0, height=4.0, angle=0.0)
    x, y = scan_coordinate_grids(frame, 2, 2, row_order="bottom_to_top")
    np.testing.assert_allclose(x, [[9.0, 11.0], [9.0, 11.0]])
    np.testing.assert_allclose(y, [[-6.0, -6.0], [-4.0, -4.0]])


def test_rotation_matches_frame_corners_convention():
    # 90 deg clockwise: corner local (w/2, h/2) maps the same way corners() does.
    frame = ScanFrame(center_x=0.0, center_y=0.0, width=2.0, height=2.0, angle=90.0)
    x, y = scan_coordinate_grids(frame, 1, 1, row_order="bottom_to_top")
    # Single pixel centre is local (0, 0) -> stays at the frame centre under rotation.
    np.testing.assert_allclose([x[0, 0], y[0, 0]], [0.0, 0.0], atol=1e-12)

    # A full-extent check against corners(): build a 2x2 grid whose pixel centres sit
    # at +/- (w/4, h/4); rotate one and compare to the same transform inline.
    from math import cos, radians, sin
    theta = radians(frame.angle)
    lx, ly = 0.5, 0.5  # local_x, local_y of the top-right pixel centre
    expected_x = lx * cos(theta) + ly * sin(theta)
    expected_y = -lx * sin(theta) + ly * cos(theta)
    gx, gy = scan_coordinate_grids(frame, 2, 2, row_order="bottom_to_top")
    np.testing.assert_allclose([gx[1, 1], gy[1, 1]], [expected_x, expected_y], atol=1e-12)


def test_rejects_bad_arguments():
    frame = ScanFrame(center_x=0.0, center_y=0.0, width=4.0, height=4.0, angle=0.0)
    with pytest.raises(ValueError, match="pixels and lines"):
        scan_coordinate_grids(frame, 0, 2, row_order="bottom_to_top")
    with pytest.raises(ValueError, match="row_order"):
        scan_coordinate_grids(frame, 2, 2, row_order="sideways")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="column_order"):
        scan_coordinate_grids(
            frame, 2, 2, row_order="bottom_to_top", column_order="up"  # type: ignore[arg-type]
        )
