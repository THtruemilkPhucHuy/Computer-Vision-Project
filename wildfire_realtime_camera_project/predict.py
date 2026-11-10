from pathlib import Path
import argparse
import torch
from PIL import Image
from torchvision import transforms, models

def load_classifier(checkpoint_path, device):
    ckpt=torch.load(checkpoint_path,map_location=device,weights_only=True)
    classes=ckpt['classes']; model=models.resnet50(weights=None,num_classes=len(classes))
    model.load_state_dict(ckpt['model_state_dict']); model.to(device).eval()
    tfm=transforms.Compose([transforms.Resize(256),transforms.CenterCrop(224),transforms.ToTensor(),transforms.Normalize(ckpt.get('mean',[.5]*3),ckpt.get('std',[.5]*3))])
    return model,classes,tfm

def predict(image_path, checkpoint='checkpoints/best_model.pth'):
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if not Path(checkpoint).is_file(): raise FileNotFoundError(f'Model not found: {checkpoint}. Train first with python train.py.')
    model,classes,tfm=load_classifier(checkpoint,device)
    with Image.open(image_path) as im: x=tfm(im.convert('RGB')).unsqueeze(0).to(device)
    with torch.inference_mode(): probs=torch.softmax(model(x),dim=1)[0]
    idx=int(probs.argmax())
    return classes[idx],float(probs[idx]),{c:float(probs[i]) for i,c in enumerate(classes)}

def main():
    p=argparse.ArgumentParser(description='Predict Fire / Neutral / Smoke for one image')
    p.add_argument('--image',required=True); p.add_argument('--checkpoint',default='checkpoints/best_model.pth'); a=p.parse_args()
    label,conf,all_probs=predict(a.image,a.checkpoint)
    print(f'Prediction: {label}\nConfidence: {conf:.2%}')
    for k,v in all_probs.items(): print(f'  {k}: {v:.2%}')
if __name__=='__main__': main()
