import cv2
import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import os

from holobot.utils.network import ZMQCameraSubscriber

def plot_tactile_sensor(ax, sensor_values, use_img=False, img=None, title='Tip Position'):
    # sensor_values: (16, 3) - 3 values for each tactile - x and y represents the position, z represents the pressure on the tactile point
    img_shape = (240, 240, 3) # For one sensor
    blank_image = np.ones(img_shape, np.uint8) * 255
    if use_img == False: 
        img = ax.imshow(blank_image.copy())
    ax.set_title(title)

    # Set the coordinates for each circle
    tactile_coordinates = []
    for j in range(48, 192+1, 48): # Y
        for i in range(48, 192+1, 48): # X - It goes from top left to bottom right row first 
            tactile_coordinates.append([i,j])

    # Plot the circles 
    for i in range(sensor_values.shape[0]):
        center_coordinates = (
            tactile_coordinates[i][0] + int(sensor_values[i,0]/20), # NOTE: Change this
            tactile_coordinates[i][1] + int(sensor_values[i,1]/20)
        )
        radius = max(10 + int(sensor_values[i,2]/10), 2)
      
        if i == 0:
            frame_axis = cv2.circle(blank_image.copy(), center_coordinates, radius, color=(0,255,0), thickness=-1)
        else:
            frame_axis = cv2.circle(frame_axis.copy(), center_coordinates, radius, color=(0,255,0), thickness=-1)

    img.set_array(frame_axis)

    return img, frame_axis

# def plot_fingertip_position(ax, tip_position, finger_index): 
#     # Tip position: (3,) - (x,y,z) positions of the tip
#     # finger_index: 0 or 1
#     types = ['X', 'Y', 'Z']
#     values = tip_position 
 
#     ax.set_ylim(-0.05, 0.15)
#     if finger_index == 0: # The index finger 
#         ax.bar(types, values, color='darkolivegreen')
#         ax.set_title('Index Finger Tip Position')
#     elif finger_index == 1:
#         ax.bar(types, values, color='mediumturquoise')
#         ax.set_title('Middle Finger Tip Position')

# TODO: Make these more general
# def dump_small_tactile_state(tactile_value, allegro_tip_pos, title='Nearest Neighbor'): # Or Current State
#     # tactile_value: (2,16,3)
#     # allegro_tip_pos: (6,)
#     fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(10,10))
#     plot_tactile_sensor(axs[0,0], tactile_value[0,:,:], title='Index Tip Tactile Sensors')
#     plot_tactile_sensor(axs[0,1], tactile_value[1,:,:], title='Middle Tip Tactile Sensors')
#     plot_fingertip_position(axs[1,0], allegro_tip_pos[0:3], 0)
#     plot_fingertip_position(axs[1,1], allegro_tip_pos[3:], 1)
#     fig.suptitle(title)
#     fig.savefig(f'{title}.png') # And we will imshow them during deployment
#     fig.clf()

def dump_camera_image(host='172.24.71.240', image_stream_port=10005):
    image_subscriber = ZMQCameraSubscriber(
        host = host,
        port = image_stream_port,
        topic_type = 'RGB'
    )
    image, _ = image_subscriber.recv_rgb_image()
    cv2.imwrite('camera_image.png', image)

# def dump_knn_state(dump_dir, img_name):
#     os.makedirs(dump_dir, exist_ok=True)
#     curr_state = cv2.imread('Current State.png')
#     knn_state = cv2.imread('Nearest Neighbor.png')
#     camera_img = cv2.imread('Camera Image.png')

#     state_img = cv2.hconcat([curr_state, knn_state])
#     width_scale = camera_img.shape[1] / state_img.shape[1]
#     state_img = cv2.resize(
#         state_img, 
#         (int(state_img.shape[1] * width_scale),
#          int(state_img.shape[0] * width_scale))
#     )

#     all_state_img = cv2.vconcat([camera_img, state_img])
#     cv2.imwrite(os.path.join(dump_dir, img_name), all_state_img)

def plot_xyz_position(ax, position, title, color='blue', ylims=None):
    types = ['X', 'Y', 'Z']
    if ylims is None:
        ax.set_ylim(-0.05, 0.15)
    else:
        ax.set_ylim(ylims)
    ax.bar(types, position, color=color)
    ax.set_title(title)

def dump_tactile_state(tactile_values):
    fig, axs = plt.subplots(nrows=4, ncols=4, figsize=(10,10))
    for col_id in range(4):
        for row_id in range(4):
            if col_id + row_id > 0:
                plot_tactile_sensor(
                    ax = axs[row_id, col_id],
                    sensor_values = tactile_values[col_id*4+row_id-1],
                    title=f'Finger: {col_id}, Sensor: {row_id}'
                )
            axs[row_id, col_id].get_yaxis().set_ticks([])
            axs[row_id, col_id].get_xaxis().set_ticks([])
    fig.savefig('tactile_state.png', bbox_inches='tight')
    fig.clf()
    plt.close()

def dump_robot_state(allegro_tip_pos, kinova_cart_pos):
    fig = plt.figure(figsize=(10,10))
    allegro_axs = []
    for i in range(2):
        for j in range(2):
            allegro_axs.append(
                plt.subplot2grid((2,4), (i,j), fig=fig)
            )
    kinova_ax = plt.subplot2grid((2,4), (0,2), colspan=2, rowspan=2, fig=fig)
    for i,ax in enumerate(allegro_axs):
        plot_xyz_position(ax = ax, position = allegro_tip_pos[i*3:(i+1)*3], title=f'Finger {i}', color='mediumturquoise', ylims=(-0.1,0.2))
        ax.get_yaxis().set_ticks([])
    plot_xyz_position(ax = kinova_ax, position = kinova_cart_pos, title=f'Arm Wrist Position', color = 'darkolivegreen', ylims=(-0.75,0.75))
    kinova_ax.get_yaxis().set_ticks([])
    plt.savefig('robot_state.png', bbox_inches='tight')
    plt.close()

def dump_whole_state(tactile_values, allegro_tip_pos, kinova_cart_pos, title='curr_state'):
    dump_tactile_state(tactile_values)
    dump_robot_state(allegro_tip_pos, kinova_cart_pos)
    tactile_state = cv2.imread('tactile_state.png')
    robot_state = cv2.imread('robot_state.png')
    state_img = concat_imgs(tactile_state, robot_state, orientation='horizontal')
    cv2.imwrite(f'{title}.png', state_img)

def dump_knn_state(dump_dir, img_name):
    os.makedirs(dump_dir, exist_ok=True)
    camera_img = cv2.imread('camera_image.png')
    knn_state = cv2.imread('knn_state.png')
    curr_state = cv2.imread('curr_state.png')

    state_img = concat_imgs(curr_state, knn_state, 'vertical')
    all_state_img = concat_imgs(camera_img, state_img, 'vertical')
    cv2.imwrite(os.path.join(dump_dir, img_name), all_state_img)


def concat_imgs(img1, img2, orientation='horizontal'): # Or it could be vertical as well
    metric_id = 0 if orientation == 'horizontal' else 1
    max_metric = max(img1.shape[metric_id], img2.shape[metric_id])
    min_metric = min(img1.shape[metric_id], img2.shape[metric_id])
    scale = min_metric / max_metric
    large_img_idx = np.argmax([img1.shape[metric_id], img2.shape[metric_id]])

    if large_img_idx == 0: 
        img1 = cv2.resize(
            img1, 
            (int(img1.shape[1]*scale),
             int(img1.shape[0]*scale))
        )
    else: 
        img2 = cv2.resize(
            img2, 
            (int(img2.shape[1]*scale),
             int(img2.shape[0]*scale))
        )

    concat_img = cv2.hconcat([img1, img2]) if orientation == 'horizontal' else cv2.vconcat([img1, img2])
    return concat_img

def turn_images_to_video(viz_dir, video_fps):
    video_path = os.path.join(viz_dir, 'visualization.mp4')
    if os.path.exists(video_path):
        os.remove(video_path)
    os.system('ffmpeg -r {} -i {}/%*.png -vf setsar=1:1 {}'.format(
        video_fps, # fps
        viz_dir,
        video_path
    ))

# Example
if __name__ == '__main__':
    model_path = '/home/irmak/Workspace/tactile-learning/tactile_learning/out/2023.01.02/19-29_byol_bs_1028_box_handle_lifting/runs'
    run_name = 'run_tactile_kinova_10cm_forward_start_ue_True' 
    turn_images_to_video(
        viz_dir = f'{model_path}/{run_name}',
        video_fps = 2
    )