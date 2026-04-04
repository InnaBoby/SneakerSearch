import torch

def get_image_embedding(image, preprocessor, model, device):

    '''
    Функция для получения эмбеддинга изображения из изображения
    '''

    preproc_image = preprocessor(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_emb = model.encode_image(preproc_image)
        
    image_emb /= image_emb.norm(dim=-1, keepdim=True)
    
    return image_emb.cpu().numpy().flatten()