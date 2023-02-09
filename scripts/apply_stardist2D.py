from omero.gateway import BlitzGateway, MapAnnotationWrapper, TagAnnotationWrapper
from omero.rtypes import rlong, rstring, robject
from omero.constants import metadata
import omero.scripts as scripts
import ezomero
import numpy as np
from stardist.models import StarDist2D
from csbdeep.utils import normalize

def add_map_annotation(conn, key_value_data, image_id):
    '''Add map annotation to image'''
    map_ann = MapAnnotationWrapper(conn)
    # Use 'client' namespace to allow editing in Insight & web
    namespace = metadata.NSCLIENTMAPANNOTATION
    map_ann.setNs(namespace)
    map_ann.setValue(key_value_data)
    map_ann.save()
    omero_image = conn.getObject("Image", image_id)
    omero_image.linkAnnotation(map_ann)
    return

def add_tag_annotation(conn, tag, image_id):
    '''Add a tag to an image'''
    tag_ann = TagAnnotationWrapper(conn)
    tag_ann.setValue(tag)
    tag_ann.save()
    omero_image = conn.getObject("Image", image_id)
    omero_image.linkAnnotation(tag_ann)
    return

def apply_stardist2D(conn, scriptParams):
    '''Apply a stardist 2D model to image(s) and saves label_image(s)'''
    # Get parameters
    dataType = scriptParams["Data_Type"]
    ids = scriptParams["IDs"]
    chosen_model = scriptParams["Available_Pretrained_Models"]
    multichannel_flag = scriptParams["Multichannel"]
    if multichannel_flag==True:
        ch = int(scriptParams["Channel_Number"])
    else:
        ch = 0
    
    
    # Get objects
    obs = conn.getObjects(dataType, ids)    # generator of images or datasets
    objects = list(obs)
    # Get list of images
    image_list, name_list = [], []
    if dataType == 'Dataset':
        dataset_id = ids[0]
        for ds in objects:
            print("Processing Images from Dataset: %s" % ds.getName())
            imgs = list(ds.listChildren())
            image_list.extend(imgs)
            name_list = [img.getName() for img in imgs]
    else:
        print("Processing Images identified by ID")
        image_list = objects
        name_list.append(image_list[0].getName())
        # get dataset
        dataset = image_list[0].getParent()
        print("From Dataset: ", dataset.getName())
        dataset_id = dataset.getId()
        
    # Stardist model
    # creates a pretrained model
    model = StarDist2D.from_pretrained(chosen_model)

    # Process images in python
    for image, name in zip(image_list, name_list):
        
        # Get image as numpy array
        pixels = image.getPrimaryPixels()
        im = pixels.getPlane(0, ch, 0)  # 2D images: z=0, c=0, t=0
        
        # Applies stardist model
        labels, _ = model.predict_instances(normalize(im))
        # Reshape to match omero standards
        labels = labels[:,:,np.newaxis, np.newaxis, np.newaxis] # make it xyzct
        # save label image in the same dataset
        label_image_name = name + "_label_" + chosen_model
        im_id = ezomero.post_image(conn, labels, label_image_name,
                                   dataset_id=dataset_id,
                                   dim_order = 'yxzct') # xyzct led to rotated
        # Add key_values indicating source image and stardist model used
        key_value_data = [["Source Image", name], 
                          ["Stardist Model", chosen_model],
                          ["Channel #", str(ch)]]
        add_map_annotation(conn, key_value_data, im_id)
        
        # Add tags indicating label image from stardist2D
        tags = ["label", "stardist2D"]
        [add_tag_annotation(conn, tag, im_id) for tag in tags]
       
    return

if __name__ == "__main__":
    """
    The main entry point of the script, as called by the client via the
    scripting service, passing the required parameters.
    """

    dataTypes = [rstring('Dataset'), rstring('Image')]
    
    available_2D_models = [rstring('2D_versatile_fluo'),
                           rstring('2D_versatile_he'),
                           rstring('2D_paper_dsb2018')]
    
    client = scripts.client(
        'Apply_stardist2D.py',

        ("Label images with Stardist"),

        scripts.String(
            "Data_Type", optional=False, grouping="1",
            description="The data you want to work with.", values=dataTypes,
            default="Dataset"),

        scripts.List(
            "IDs", optional=False, grouping="2",
            description="List of Dataset IDs or Image IDs").ofType(rlong(0)),
        
        scripts.String(
            "Available_Pretrained_Models", optional=False, grouping="3",
            description="List of available pretrained Stardist models",
            values = available_2D_models, default="2D_versatile_fluo"),
        
        # If multichannel, ask which channel contains nuclei
        scripts.Bool("Multichannel", grouping="4", default=False),
        
        scripts.String(
            "Channel_Number", optional=True, grouping="4.1",
            description="The channel number (first channel is 0).")
        
        # TO DO: allow using custom stardist2D model from file
        # scripts.Bool("Use_Custom_Model", grouping="4", default=False),
        
        # scripts.String(
        #     "Model_Name", optional=True, grouping="4.1",
        #     description="The model file name.")
        
        )
    
    try:
        # Get parameters
        scriptParams = {}
        for key in client.getInputKeys():
            if client.getInput(key):
                # unwrap rtypes to String, Integer etc
                scriptParams[key] = client.getInput(key, unwrap=True)

        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)

        # process images
        processed_images = apply_stardist2D(conn, scriptParams)

    finally:
        client.closeSession()