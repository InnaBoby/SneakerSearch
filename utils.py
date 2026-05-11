import torch
from torchvision import transforms

def get_clip_embedding(image, preprocessor, model, device):

    '''
    Функция для получения эмбеддинга изображения из изображения
    '''

    preproc_image = preprocessor(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_emb = model.encode_image(preproc_image)
        
    image_emb /= image_emb.norm(dim=-1, keepdim=True)
    
    return image_emb.cpu().numpy().flatten()


def sneakers_classifier(image, model, device):

    #трансформации для mobilenet
    mobilenet_preprocess = transforms.Compose([
        transforms.Resize(256),                  # изменяем размер меньшей стороны до 256
        transforms.CenterCrop(224),              # обрезаем центр до 224x224
        transforms.ToTensor(),                   # переводим в тензор и нормализуем в [0, 1]
        transforms.Normalize(                    # стандартная нормализация для ImageNet
            mean=[0.485, 0.456, 0.406], 
            std=[0.229, 0.224, 0.225]
        ),
    ])

    prerpoc_image = mobilenet_preprocess(image)                     
    input = torch.unsqueeze(prerpoc_image, 0) 
    input = input.to(device)
         
    with torch.no_grad():
        output = model(input)

    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    #print(f"Вероятность кроссовок: {probabilities[0].item():.2%}")
    return probabilities[0].item()